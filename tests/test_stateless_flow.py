import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json
from app.main import app
from app.schemas import Message

# Mock the LLM client to avoid making real API calls
mock_llm_client = AsyncMock()

# Setup the mock response for chat generation
async def mock_generate_chat_response(messages, stream=False, model=None):
    from types import SimpleNamespace
    # Return a simple mock object with a message content
    return SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content="This is a mock response."))
    ])

mock_llm_client.generate_chat_response = mock_generate_chat_response
mock_llm_client.summarize_conversation.return_value = "Mocked Summary"

# Create TestClient
client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch('app.routers.chat.llm_client', mock_llm_client):
        yield

def test_single_message(mock_dependencies):
    """Test sending a single message without history."""
    payload = {
        "message": "Hello",
        "messages": [],
        "summary": None
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["response"] == "This is a mock response."
    # Check updated history: should be [User, Assistant]
    assert len(data["updated_history"]) == 2
    assert data["updated_history"][0]["role"] == "user"
    assert data["updated_history"][0]["content"] == "Hello"
    assert data["updated_history"][1]["role"] == "assistant"
    assert data["updated_history"][1]["content"] == "This is a mock response."

def test_conversation_continuity(mock_dependencies):
    """Test continuing a conversation by passing history back."""
    # Simulate existing history
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello there."}
    ]
    payload = {
        "message": "How are you?",
        "messages": history,
        "summary": None
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check updated history: should be [User, Assistant, User, Assistant] (4 messages)
    assert len(data["updated_history"]) == 4
    assert data["updated_history"][2]["content"] == "How are you?"
    assert data["updated_history"][3]["content"] == "This is a mock response."

def test_summarization_trigger(mock_dependencies):
    """Test that summarization triggers when history is long."""
    # Create a long history (e.g., 20 messages)
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    
    payload = {
        "message": "Trigger Summary",
        "messages": long_history,
        "summary": "Old Summary"
    }
    
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check if summary updated
    assert data["updated_summary"] == "Mocked Summary"
    
    # Check if history truncated
    # Logic: It keeps last 5 messages + adds new user + new assistant = 7 total
    assert len(data["updated_history"]) == 7
    # Verify the last message is the assistant response
    assert data["updated_history"][-1]["role"] == "assistant"
