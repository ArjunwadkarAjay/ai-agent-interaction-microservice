from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    messages: List[Message] = []
    summary: Optional[str] = None
    domain: Optional[str] = None
    stream: bool = False
    model: Optional[str] = None
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    updated_summary: Optional[str] = None
    updated_history: List[Message] = []

class UploadResponse(BaseModel):
    id: int
    filename: str
    domain: str
    file_path: str
    created_at: datetime
    status: str
