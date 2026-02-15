from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import ChatSession, Message
from uuid import UUID

async def create_chat_session(db: AsyncSession, domain: str = None):
    db_session = ChatSession(domain_name=domain)
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_chat_session(db: AsyncSession, session_id: UUID):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    return result.scalars().first()

async def update_session_summary(db: AsyncSession, session_id: UUID, summary: str):
    db_session = await get_chat_session(db, session_id)
    if db_session:
        db_session.summary = summary
        await db.commit()
        await db.refresh(db_session)
    return db_session

async def add_message(db: AsyncSession, session_id: UUID, role: str, content: str):
    db_message = Message(session_id=session_id, role=role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_recent_messages(db: AsyncSession, session_id: UUID, limit: int = 15):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages)) # Return in chronological order

async def create_document(db: AsyncSession, filename: str, domain: str, file_path: str):
    from app.models import Document
    db_document = Document(filename=filename, domain=domain, file_path=file_path)
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document
