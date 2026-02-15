from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch("app.routers.chat.crud")
@patch("app.routers.chat.llm_client")
@patch("app.routers.chat.vector_store")
def test_chat_endpoint(mock_vector_store, mock_llm_client, mock_crud):
    # Mock DB Interaction
    mock_crud.get_chat_session.return_value = MagicMock(id="1234", summary="Test Summary")
    mock_crud.create_chat_session.return_value = MagicMock(id="1234")
    mock_crud.get_recent_messages.return_value = []
    
    # Mock LLM Interaction
    mock_llm_client.generate_chat_response.return_value.choices = [
        MagicMock(message=MagicMock(content="Hello!"))
    ]

    response = client.post("/api/v1/chat", json={"message": "Hi", "domain": "test_domain"})
    assert response.status_code == 200
    assert response.json()["response"] == "Hello!"

@patch("app.routers.document.vector_store")
def test_upload_endpoint(mock_vector_store):
    files = {'file': ('test.txt', b'test content', 'text/plain')}
    data = {'domain': 'test_domain'}
    response = client.post("/api/v1/upload", files=files, data=data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
