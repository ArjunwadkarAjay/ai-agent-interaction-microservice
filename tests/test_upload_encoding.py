import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

from unittest.mock import patch

def test_upload_invalid_utf8():
    # Mock the vector store to avoid embedding computation/download
    with patch("app.routers.document.vector_store.add_documents") as mock_add_docs:
        # 0xd3 is invalid in UTF-8 context here
        content = b"Invalid content: \xd3"
        files = {"file": ("test_file.txt", content, "text/plain")}
        data = {"domain": "test-domain"}
    
    
        # This triggers the upload endpoint
        response = client.post("/api/v1/upload", files=files, data=data)
        
        # We expect this to SUCCEED with 200 OK after the fix.
        # If the bug is present, this assertion will fail (500 != 200).
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
        
        json_response = response.json()
        assert json_response["status"] == "success"
        
        # Verify file persistence
        import os
        assert os.path.exists("uploads/test_file.txt"), "Uploaded file was not saved to disk!"
        
        # Clean up
        if os.path.exists("uploads/test_file.txt"):
            os.remove("uploads/test_file.txt")
