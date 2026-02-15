# Local AI Agent App

A generalized AI agent application that interacts with any OpenAI-compliant inference endpoint. It features persistent conversation history, domain-specific document management with vector search, and automatic summarization.

## Features

- **OpenAI-Compatible Inference**: Works with any provider (OpenAI, LocalAI, vLLM, etc.).
- **Smart Conversation History**:
  - Automatically summarizes conversations exceeding a configurable threshold.
  - Initial system prompt injected with summary and relevant context.
- **Domain-Specific Knowledge**:
  - Upload documents (TXT, etc.) associated with specific "Domains".
  - Documents are chunked, embedded in ChromaDB, and **persisted to disk**.
  - Relevant context is retrieved during chats based on the specified domain.
- **Robust Persistence**:
  - **PostgreSQL**: Stores `ChatSession` history, `Message` logs, and `Document` metadata.
  - **ChromaDB**: Stores vector embeddings.
  - **File System**: Original uploaded files are safely stored in `uploads/`.

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (Async SQLAlchemy + Alembic Migrations)
- **Vector Store**: ChromaDB
- **Infrastructure**: Docker & Docker Compose

## Quick Start

1. **Configure Environment**
   Copy `.env.example` to `.env` and update values:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

2. **Run with Docker**
   Build and start the services. This automatically runs database migrations on startup.
   ```bash
   docker-compose up --build
   ```

   - API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## API Endpoints

### `POST /api/v1/chat`
Interact with the agent.
- **Body**:
  ```json
  {
    "message": "Hello world",
    "domain": "my-website",
    "session_id": "optional-uuid",
    "stream": true
  }
  ```

### `POST /api/v1/upload`
Upload a document for a specific domain.
- **Form Data**:
  - `file`: The file to upload.
  - `domain`: Target domain name (e.g., "docs-v1").

## Development

- **Migrations**: managed by Alembic.
  ```bash
  # Create a new migration (requires local DB connection)
  alembic revision --autogenerate -m "message"
  
  # Apply migrations manually
  docker-compose exec app alembic upgrade head
  ```
