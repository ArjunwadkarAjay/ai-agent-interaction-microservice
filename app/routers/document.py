from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.vector_store import vector_store
from app.schemas import UploadResponse
import uuid

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(...)
):
    try:
        # 1. Processing in Memory
        # We do NOT save to disk as per "no persistence" requirement.
        
        # 2. Read File Content
        content = await file.read()
        
        # Virtual path for metadata (not used for actual retrieval)
        file_path = f"memory://{domain}/{file.filename}"

        # 3. Track in DB - SKIPPED (Stateless)
        # db_document = await crud.create_document(db, file.filename, domain, file_path)
        
        # 4. Process Content for ChromaDB
        text_content = content.decode("utf-8") # Simplified text extraction (improve for PDF/DOCX)
        
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
            created_at=uuid.uuid1().time, # Dummy timestamp or use datetime.now() if schema allows
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
