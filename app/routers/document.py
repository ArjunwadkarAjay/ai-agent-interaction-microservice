from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.vector_store import vector_store
from app.schemas import UploadResponse
import uuid
from datetime import datetime

router = APIRouter()

import os
import shutil
from app.config import settings

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(...)
):
    try:
        # 1. Processing and Persistence
        # Ensure upload directory exists - Create domain specific folder
        domain_path = os.path.join(settings.UPLOAD_DIR, domain)
        os.makedirs(domain_path, exist_ok=True)
        
        # Define file path
        # Ideally we should sanitize filename or use a UUID to prevent collisions/security issues
        # But keeping it simple as per current requirement
        file_path = os.path.join(domain_path, file.filename)
        
        # Save to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Read File Content (for embedding)
        # We can read from the saved file now, or just seek back the UploadFile if we didn't close it
        # Since shutil.copyfileobj might consume the file, let's read from the saved file to be safe
        with open(file_path, "rb") as f:
            content = f.read()

        # 3. Track in DB - SKIPPED (Stateless)
        # db_document = await crud.create_document(db, file.filename, domain, file_path)
        
        # 4. Process Content for ChromaDB
        text_content = content.decode("utf-8", errors="replace") # Simplified text extraction (improve for PDF/DOCX)
        
        # Simple chunking logic (can be improved)
        chunks = [text_content[i:i+1000] for i in range(0, len(text_content), 1000)]
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": file.filename, "domain": domain, "path": file_path} for _ in chunks]

        vector_store.add_documents(domain, chunks, metadatas, ids)

        # Return dummy ID since we don't have a DB
        return UploadResponse(
            id=0,
            filename=file.filename,
            domain=domain,
            file_path=file_path,
            created_at=datetime.now(), # Dummy timestamp or use datetime.now() if schema allows
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import List
from app.schemas import DocumentInfo
import pathlib

@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all uploaded documents, inferring domain from folder structure.
    Structure expected: uploads/{domain}/{filename} via standard upload? 
    Current upload just puts in uploads root. 
    But user wants to "tell from update folders what domain they are under".
    So we will scan subdirectories.
    """
    documents = []
    upload_path = pathlib.Path(settings.UPLOAD_DIR)
    
    if not upload_path.exists():
        return []

    # Walk through directory
    for root, dirs, files in os.walk(upload_path):
        for file in files:
            if file.startswith("."): continue # Skip hidden files
            
            full_path = pathlib.Path(root) / file
            relative_path = full_path.relative_to(upload_path)
            
            # Domain logic: 
            # If directly in uploads -> "general"
            # If in uploads/subdir -> "subdir"
            parent = relative_path.parent
            if str(parent) == ".":
                domain = "general"
            else:
                # Use the first part of the path as domain
                domain = str(parent)
            
            stat = full_path.stat()
            
            doc = DocumentInfo(
                filename=file,
                domain=domain,
                path=str(full_path),
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime)
            )
            documents.append(doc)
            
    return documents

