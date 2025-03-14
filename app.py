from langchain_community.vectorstores import FAISS
from pydantic import BaseModel
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi import FastAPI, HTTPException
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
import uvicorn
import pyngrok
from langchain.schema import messages_from_dict, messages_to_dict

app = FastAPI(
    title="FastAPI Demo",
    version="0.1",
    description="This API provides a simple interface for querying a Bible database using natural language. It leverages advanced language models to generate answers and maintains a chat history for each user session"
)

# MongoDB configuration
MONGODB_URI = "mongodb://localhost:27017"
client = MongoClient(MONGODB_URI)
db = client["bible_db"]
collection = db["chat_history"]

# Embeddings and vector store
embeddings = OllamaEmbeddings(model="llama2:7b")
faiss_vectordb = FAISS.load_local(
    "combined_index", embeddings, allow_dangerous_deserialization=True
)

# Retriever
retriever = faiss_vectordb.as_retriever()

# LLM
llm = Ollama(model="llama2:7b")

# System prompts
system_prompt = (
    "Use the following pieces of context to answer the question. "
    "If you don't know the answer, just say that you don't know, don't try to make up an answer. "
    "Don't exaggerate the answer and keep the answer as concise as possible. "
    "Do not include the question in the answer or use phrases like 'Thank you for your question' or 'The question you provided'. "
    "You do not have to say thank you or include any introductory or closing phrases, "
    "and you can directly respond to the query without mentioning the context to the passage phrase. "
    "You don't have to say 'The passage you provided' or 'In the passage' in the answer, directly quote the bible. "
    "Tell it that this is the bible and it has to answer quoting it. "
    "Just start directly with the answer. "
    "\n\n"
    "{context}"
)

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

# Prompts
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# History-aware retriever and chain
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# Define Pydantic model for request body
class QueryRequest(BaseModel):
    query: str
    session_id: str  # You can use int if session IDs are numeric

@app.post("/ask_query")
def ask_query(request: QueryRequest):
    try:
        question = request.query
        session_id = request.session_id

        # Retrieve chat history from MongoDB for the given session_id
        chat_history_doc = collection.find_one({"_id": session_id})
        if chat_history_doc is None:
            chat_history = []
        else:
            chat_history = messages_from_dict(chat_history_doc.get("history", []))

        # Invoke the chain with the question and chat history
        ai_response = rag_chain.invoke({"input": question, "chat_history": chat_history})

        # Extend the chat history with the new interaction
        chat_history.extend([
            HumanMessage(content=question),
            AIMessage(content=ai_response["answer"]),
        ])

        # Serialize and update chat history in MongoDB
        serialized_chat_history = messages_to_dict(chat_history)
        collection.update_one(
            {"_id": session_id},
            {"$set": {"history": serialized_chat_history}},
            upsert=True
        )

        # Return the answer
        return {"answer": ai_response["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_chat_history")
def get_chat_history(session_id: str):
    try:
        # Retrieve chat history from MongoDB for the given session_id
        chat_history_doc = collection.find_one({"_id": session_id})
        if chat_history_doc is None:
            return {"message": "No chat history found for this session_id."}
        else:
            # Deserialize the messages
            chat_history = messages_from_dict(chat_history_doc.get("history", []))
            # Convert messages to a list of dictionaries for serialization
            serialized_history = []
            for message in chat_history:
                if isinstance(message, HumanMessage):
                    serialized_history.append({
                        "role": "user",
                        "content": message.content
                    })
                elif isinstance(message, AIMessage):
                    serialized_history.append({
                        "role": "assistant",
                        "content": message.content
                    })
            return {"chat_history": serialized_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_chat_history")
def delete_chat_history(session_id: str):
    try:
        result = collection.delete_one({"_id": session_id})
        if result.deleted_count == 1:
            return {"message": f"Chat history for session_id {session_id} deleted successfully."}
        else:
            return {"message": f"No chat history found for session_id {session_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run FastAPI app using Uvicorn server
    uvicorn.run(app, host="localhost", port=8000)  