from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc
from app.models.chat import ChatSession, ChatMessage


async def create_session(db: AsyncSession, **kwargs) -> ChatSession:
    session = ChatSession(**kwargs)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: int) -> Optional[ChatSession]:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    return result.scalar_one_or_none()


async def get_sessions_by_user(
    db: AsyncSession, user_id: int, workspace_id: int,
    page: int = 1, per_page: int = 20
) -> Tuple[List[ChatSession], int]:
    query = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.workspace_id == workspace_id,
        ChatSession.is_active == True,
    )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(desc(ChatSession.updated_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return result.scalars().all(), total or 0


async def create_message(db: AsyncSession, **kwargs) -> ChatMessage:
    msg = ChatMessage(**kwargs)
    db.add(msg)
    # Increment session message count
    await db.execute(
        update(ChatSession)
        .where(ChatSession.id == kwargs["session_id"])
        .values(message_count=ChatSession.message_count + 1)
    )
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages_by_session(
    db: AsyncSession, session_id: int
) -> List[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


async def update_session_title(db: AsyncSession, session_id: int, title: str):
    await db.execute(
        update(ChatSession).where(ChatSession.id == session_id).values(title=title)
    )
    await db.commit()


async def delete_session(db: AsyncSession, session_id: int):
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.execute(delete(ChatSession).where(ChatSession.id == session_id))
    await db.commit()


async def update_message_feedback(db: AsyncSession, message_id: int, feedback: str):
    await db.execute(
        update(ChatMessage).where(ChatMessage.id == message_id).values(feedback=feedback)
    )
    await db.commit()
