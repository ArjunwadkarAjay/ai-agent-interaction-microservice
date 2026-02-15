from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.vector_store import vector_store
from app.schemas import UploadResponse
from app.config import settings
from app.database import get_db
from app import crud
import uuid
import os
import shutil

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Prepare Directory
        upload_path = os.path.join(settings.UPLOAD_DIR, domain)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, file.filename)

        # 2. Save File to Disk
        # We read into memory first to simplify both saving and processing (text extraction)
        # For very large files, this should be streamed, but for this agent context, it's acceptable.
        content = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # 3. Track in DB
        await crud.create_document(db, file.filename, domain, file_path)

        # 4. Process Content for ChromaDB
        text_content = content.decode("utf-8") # Simplified text extraction (improve for PDF/DOCX)
        
        # Simple chunking logic (can be improved)
        chunks = [text_content[i:i+1000] for i in range(0, len(text_content), 1000)]
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": file.filename, "domain": domain, "path": file_path} for _ in chunks]

        vector_store.add_documents(domain, chunks, metadatas, ids)

        return UploadResponse(filename=file.filename, domain=domain, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
