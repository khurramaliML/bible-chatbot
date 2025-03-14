# FastAPI Bible API Documentation

**Version**: 0.1  
**Description**: This API provides a simple interface for querying a Bible database using natural language. It leverages advanced language models to generate answers and maintains a chat history for each user session.

## Overview

The FastAPI Demo API allows users to:

- Ask questions related to the Bible and receive concise answers.
- Maintain a chat history for each session to provide context in conversations.
- Retrieve and delete chat history associated with a specific session.

The API uses advanced language models (LLMs) and embeddings to understand and process queries. Chat histories are stored in a MongoDB database for persistence across sessions.

## Run Server

```plaintext
 python app.py
```

## Base URL

```plaintext
http://localhost:8000/
```

## Endpoints

### POST /ask_query

Submits a query and returns an answer, maintaining the chat history for the session.

- **URL**: `/ask_query`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**: JSON object conforming to the `QueryRequest` model.
- **Response**: JSON object containing the answer.
- **Status Codes**:
  - `200 OK`: Successful response.
  - `500 Internal Server Error`: Server error occurred.

#### Request Body Parameters

- `query` (string, required): The question to be asked.
- `session_id` (string, required): Unique identifier for the user's session.

#### Response Body

- `answer` (string): The generated answer to the query.

#### Example Request

```json
{
  "query": "What does the Bible say about faith?",
  "session_id": "session_123"
}
```

#### Example Response

```json
{
  "answer": "Faith is the assurance of things hoped for, the conviction of things not seen."
}
```

### GET /get_chat_history

Retrieves the chat history for a given session ID.

- **URL**: `/get_chat_history`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id` (string, required): The session ID.
- **Response**: JSON object containing the chat history or a message.
- **Status Codes**:
  - `200 OK`: Successful response.
  - `500 Internal Server Error`: Server error occurred.

#### Response Body

- If chat history exists:
  - `chat_history` (array): List of message objects containing `role` and `content`.
- If no chat history:
  - `message` (string): Informational message.

#### Example Request

```plaintext
GET /get_chat_history?session_id=session_123
```

#### Example Response (Chat History Exists)

```json
{
  "chat_history": [
    {"role": "user", "content": "What is love according to the Bible?"},
    {"role": "assistant", "content": "Love is patient and kind; it does not envy or boast."}
  ]
}
```

#### Example Response (No Chat History)

```json
{
  "message": "No chat history found for this session_id."
}
```

### DELETE /delete_chat_history

Deletes the chat history associated with a given session ID.

- **URL**: `/delete_chat_history`
- **Method**: `DELETE`
- **Query Parameters**:
  - `session_id` (string, required): The session ID.
- **Response**: JSON object containing a message about the deletion status.
- **Status Codes**:
  - `200 OK`: Successful deletion or no history found.
  - `500 Internal Server Error`: Server error occurred.

#### Response Body

- `message` (string): Information about the deletion outcome.

#### Example Request

```plaintext
DELETE /delete_chat_history?session_id=session_123
```

#### Example Response (Deletion Successful)

```json
{
  "message": "Chat history for session_id session_123 deleted successfully."
}
```

#### Example Response (No Chat History Found)

```json
{
  "message": "No chat history found for session_id session_123."
}
```

## Data Models

### QueryRequest

Model for the request body when asking a query.

- **Fields**:
  - `query` (string, required): The user's question.
  - `session_id` (string, required): Unique session identifier.

#### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "session_id": {"type": "string"}
  },
  "required": ["query", "session_id"]
}
```

## Examples

### Asking a Query

**Request**

```plaintext
POST /ask_query
Content-Type: application/json

{
  "query": "Who was Moses?",
  "session_id": "session_456"
}
```

**Response**

```json
{
  "answer": "Moses was a prophet who led the Israelites out of Egypt and received the Ten Commandments."
}
```

### Retrieving Chat History

**Request**

```plaintext
GET /get_chat_history?session_id=session_456
```

**Response**

```json
{
  "chat_history": [
    {"role": "user", "content": "Who was Moses?"},
    {
      "role": "assistant",
      "content": "Moses was a prophet who led the Israelites out of Egypt and received the Ten Commandments."
    }
  ]
}
```

### Deleting Chat History

**Request**

```plaintext
DELETE /delete_chat_history?session_id=session_456
```

**Response**

```json
{
  "message": "Chat history for session_id session_456 deleted successfully."
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of an API request. In case of errors, a JSON response with a `detail` field provides more information.

- **500 Internal Server Error**

  - **Cause**: An exception occurred during request processing.
  - **Response**:

    ```json
    {
      "detail": "Error message describing what went wrong."
    }
    ```

## Additional Notes

- **Session Management**: Use unique `session_id` values to maintain separate chat histories for different users or sessions.
- **Database**: MongoDB is used for storing chat histories under the `bible_db` database and `chat_history` collection.
- **Language Model**: The API utilizes the Llama 2 (7b) model for generating responses, accessed via the `Ollama` interface.
- **Embeddings and Vector Store**: FAISS is used as the vector store, with embeddings provided by `OllamaEmbeddings`.
- **Contextual Understanding**: The API is designed to understand context from previous interactions in the chat history.
- **Prompts and Templates**: Custom prompts are used to ensure the language model provides concise and relevant answers without unnecessary phrasing.