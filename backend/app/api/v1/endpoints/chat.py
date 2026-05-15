from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.rag_engine.engine import RAGEngine
from app.crud.chat import (
    create_session, get_session, get_sessions_by_user,
    create_message, get_messages_by_session,
    update_session_title, delete_session
)
from app.crud.query_log import create_query_log
from loguru import logger
import time

router = APIRouter(prefix="/chat", tags=["Chat"])
rag_engine = RAGEngine()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    workspace_id: int
    model: str = "gpt-4o"
    filter_doc_ids: Optional[List[int]] = None
    stream: bool = False


class NewSessionRequest(BaseModel):
    workspace_id: int
    title: Optional[str] = None
    model: str = "gpt-4o"


@router.post("/sessions")
async def create_chat_session(
    request: NewSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await create_session(
        db=db,
        user_id=current_user.id,
        workspace_id=request.workspace_id,
        title=request.title or "New Chat",
        model=request.model,
    )
    return _session_dict(session)


@router.get("/sessions")
async def list_sessions(
    workspace_id: int = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sessions, total = await get_sessions_by_user(
        db, current_user.id, workspace_id, page=page, per_page=per_page
    )
    return {
        "sessions": [_session_dict(s) for s in sessions],
        "total": total,
        "page": page,
    }


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await get_messages_by_session(db, session_id)
    return {"messages": [_message_dict(m) for m in messages]}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    await delete_session(db, session_id)
    return {"message": "Session deleted"}


@router.post("/message")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get RAG response (non-streaming)"""
    start_time = time.time()

    # Get or create session
    if request.session_id:
        session = await get_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = await create_session(
            db=db,
            user_id=current_user.id,
            workspace_id=request.workspace_id,
            title=request.message[:50],
            model=request.model,
        )

    # Get conversation history
    history_messages = await get_messages_by_session(db, session.id)
    history = [{"role": m.role, "content": m.content} for m in history_messages[-20:]]

    # Save user message
    await create_message(
        db=db, session_id=session.id,
        role="user", content=request.message
    )

    # Run RAG
    try:
        result = await rag_engine.query(
            question=request.message,
            workspace_id=request.workspace_id,
            model=request.model,
            conversation_history=history,
            filter_doc_ids=request.filter_doc_ids,
        )

        answer = result["answer"]
        sources = result["sources"]
        latency = (time.time() - start_time) * 1000

        # Save assistant message
        assistant_msg = await create_message(
            db=db,
            session_id=session.id,
            role="assistant",
            content=answer,
            sources=sources,
            model=request.model,
            latency_ms=latency,
        )

        # Log query
        await create_query_log(
            db=db,
            user_id=current_user.id,
            workspace_id=request.workspace_id,
            session_id=session.id,
            query=request.message,
            response_preview=answer[:500],
            model_used=request.model,
            latency_ms=latency,
        )

        # Auto-title session after first exchange
        if session.message_count == 0:
            await update_session_title(db, session.id, request.message[:60])

        return {
            "session_id": session.id,
            "message_id": assistant_msg.id,
            "answer": answer,
            "sources": sources,
            "latency_ms": latency,
            "model": request.model,
        }

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream RAG response using Server-Sent Events"""
    # Get or create session
    if request.session_id:
        session = await get_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = await create_session(
            db=db,
            user_id=current_user.id,
            workspace_id=request.workspace_id,
            title=request.message[:50],
            model=request.model,
        )

    history_messages = await get_messages_by_session(db, session.id)
    history = [{"role": m.role, "content": m.content} for m in history_messages[-20:]]

    # Save user message
    await create_message(db=db, session_id=session.id, role="user", content=request.message)

    async def generate():
        full_response = []
        sources = []
        try:
            async for chunk in rag_engine.stream_query(
                question=request.message,
                workspace_id=request.workspace_id,
                model=request.model,
                conversation_history=history,
                filter_doc_ids=request.filter_doc_ids,
            ):
                yield chunk
                import json as _json
                try:
                    data = _json.loads(chunk.replace("data: ", "").strip())
                    if data.get("type") == "token":
                        full_response.append(data.get("content", ""))
                    elif data.get("type") == "sources":
                        sources = data.get("sources", [])
                except Exception:
                    pass
        except Exception as e:
            import json as _json
            yield f"data: {_json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Save final response to DB
        if full_response:
            answer = "".join(full_response)
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as save_db:
                await create_message(
                    db=save_db,
                    session_id=session.id,
                    role="assistant",
                    content=answer,
                    sources=sources,
                    model=request.model,
                )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": str(session.id),
        }
    )


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(
    message_id: int,
    feedback: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit thumbs up/down feedback on a response"""
    from app.crud.chat import update_message_feedback
    await update_message_feedback(
        db, message_id, feedback.get("rating")  # "positive" | "negative"
    )
    return {"message": "Feedback recorded"}


def _session_dict(session: ChatSession) -> dict:
    return {
        "id": session.id,
        "title": session.title,
        "model": session.model,
        "message_count": session.message_count,
        "workspace_id": session.workspace_id,
        "created_at": str(session.created_at),
        "updated_at": str(session.updated_at),
    }


def _message_dict(msg: ChatMessage) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "sources": msg.sources,
        "model": msg.model,
        "tokens_used": msg.tokens_used,
        "latency_ms": msg.latency_ms,
        "feedback": msg.feedback,
        "created_at": str(msg.created_at),
    }
