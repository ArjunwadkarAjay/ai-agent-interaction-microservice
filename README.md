# Local AI Agent App

A high-performance, stateless AI agent application designed for local deployment. It features **WebSocket streaming**, **domain-aware RAG (Retrieval-Augmented Generation)**, and **automatic conversation summarization**.

## 🚀 Features

-   **Stateless Architecture**:
    -   No database dependency for chat history.
    -   Conversation state (history & summary) is managed by the client and passed in each request.
    -   ideal for scalable, cloud-native deployments.

-   **Real-time Streaming**:
    -   **WebSocket API**: Low-latency streaming of generated text.
    -   **Standard HTTP**: Traditional request-response API for non-streaming use cases.

-   **Domain-Specific RAG**:
    -   **Uploads**: Organize documents into "Domains" (folders).
    -   **Search Modes**:
        -   **No Context**: Pure LLM interaction.
        -   **All Domains**: Search across the entire knowledge base.
        -   **Specific Domain**: Filter search results to a single domain.

-   **Smart Summarization**:
    -   **Loopback Logic**: Summaries are generated when conversation length exceeds a threshold (`SUMMARY_THRESHOLD`).
    -   **Token Limits**: Summaries are strictly capped (`SUMMARY_MAX_TOKENS`) to prevent context bloat.
    -   **Persistence**: The summary is returned to the client and re-injected in future requests to maintain long-term context.

-   **Customizable Persona**:
    -   **System Prompt**: Configurable via API/UI to change the agent's behavior (e.g., "You are a pirate").
    -   **Parameters**: Fine-tune `temperature`, `top_p`, `max_tokens`, etc.

## 🛠️ Tech Stack

-   **Backend**: FastAPI (Python 3.11)
-   **Vector Store**: ChromaDB (Persistent storage in Docker volume)
-   **LLM Interface**: OpenAI-compatible client (works with LocalAI, vLLM, Ollama, etc.)
-   **Frontend**: Streamlit (for testing and interaction)
-   **Containerization**: Docker & Docker Compose

## ⚡ Quick Start

### 1. Configure Environment
Copy the example configuration:
```bash
cp .env.example .env
```
Edit `.env` to set your model details and preferences:
```ini
OPENAI_API_KEY=sk-xxx (or 'none' for local)
OPENAI_BASE_URL=http://host.docker.internal:8080/v1
MODEL_NAME=gpt-3.5-turbo (or your local model name)
SUMMARY_THRESHOLD=15
SUMMARY_MAX_TOKENS=200
```

### 2. Run with Docker
Build and start the services:
```bash
docker-compose up --build
```
-   **API**: `http://localhost:8000`
-   **Streamlit UI**: `http://localhost:8501`

## 📚 API Reference

### WebSocket Chat (Streaming)
**Endpoint**: `ws://localhost:8000/api/v1/ws/chat`

**Payload**:
```json
{
  "message": "Hello!",
  "messages": [{"role": "user", "content": "..."}],
  "summary": "Previous summary...",
  "domain": "finance",
  "system_prompt": "You are a financial advisor.",
  "stream": true
}
```

**Response Stream**:
-   `{"content": "..."}` (Generated text chunks)
-   `{"metadata": {"updated_summary": "...", "updated_history": [...]}}` (Final packet)

### HTTP Chat (Non-Streaming)
**Endpoint**: `POST /api/v1/chat`

**Body**: Same as WebSocket payload.

**Response**:
```json
{
  "response": "Full generated text.",
  "updated_summary": "...",
  "updated_history": [...]
}
```

### Document Management
-   **List Documents**: `GET /api/v1/documents`
-   **Upload Document**: `POST /api/v1/upload`
    -   Form Data: `file` (binary), `domain` (string)

## 🖥️ Streamlit UI

The included Streamlit app provides a complete interface for:
-   **Chat**: Interact with the agent, toggle streaming, and view history.
-   **Management**: Upload files to specific domains and view existing documents.
-   **Configuration**: Adjust system prompt, model parameters, and search scope in real-time.

To run locally (outside Docker):
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
