from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, document
# Database deps removed
import asyncio

app = FastAPI(title="Local AI Agent App")

# Tables should be managed via Alembic migrations

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Local AI Agent App"}
