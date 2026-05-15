from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.dependencies import get_current_admin_user, get_db
from app.models.user import User
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.chat import ChatSession

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin dashboard metrics"""
    # User stats
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )

    # Document stats
    total_docs = await db.scalar(select(func.count(Document.id)))
    indexed_docs = await db.scalar(
        select(func.count(Document.id)).where(Document.status == "indexed")
    )
    pending_docs = await db.scalar(
        select(func.count(Document.id)).where(Document.status == "processing")
    )

    # Query stats
    total_queries = await db.scalar(select(func.count(QueryLog.id)))
    total_sessions = await db.scalar(select(func.count(ChatSession.id)))

    # Recent queries
    recent_queries_result = await db.execute(
        select(QueryLog)
        .order_by(desc(QueryLog.created_at))
        .limit(10)
    )
    recent_queries = recent_queries_result.scalars().all()

    # Usage by model
    model_usage_result = await db.execute(
        select(QueryLog.model_used, func.count(QueryLog.id).label("count"))
        .group_by(QueryLog.model_used)
        .order_by(desc("count"))
    )
    model_usage = [{"model": row[0], "count": row[1]} for row in model_usage_result]

    # Avg latency
    avg_latency = await db.scalar(select(func.avg(QueryLog.latency_ms)))

    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "documents": {
            "total": total_docs,
            "indexed": indexed_docs,
            "processing": pending_docs,
            "failed": total_docs - (indexed_docs or 0) - (pending_docs or 0),
        },
        "queries": {
            "total": total_queries,
            "sessions": total_sessions,
            "avg_latency_ms": round(avg_latency or 0, 2),
        },
        "model_usage": model_usage,
        "recent_queries": [
            {
                "id": q.id,
                "query": q.query[:100],
                "model": q.model_used,
                "latency_ms": q.latency_ms,
                "created_at": str(q.created_at),
            }
            for q in recent_queries
        ],
    }


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if search:
        query = query.where(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(desc(User.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "organization": u.organization,
                "last_login": str(u.last_login),
                "created_at": str(u.created_at),
            }
            for u in users
        ],
        "total": total,
        "page": page,
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = {"role", "is_active", "organization", "department"}
    for key, value in update_data.items():
        if key in allowed:
            setattr(user, key, value)

    await db.commit()
    return {"message": "User updated", "user_id": user_id}


@router.get("/query-logs")
async def get_query_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(QueryLog)
    if workspace_id:
        query = query.where(QueryLog.workspace_id == workspace_id)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(desc(QueryLog.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": l.id,
                "query": l.query[:200],
                "model_used": l.model_used,
                "latency_ms": l.latency_ms,
                "success": l.success,
                "user_id": l.user_id,
                "workspace_id": l.workspace_id,
                "created_at": str(l.created_at),
            }
            for l in logs
        ],
        "total": total,
        "page": page,
    }


@router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Daily usage analytics"""
    from datetime import datetime, timedelta
    start_date = datetime.utcnow() - timedelta(days=days)

    # Queries per day
    daily_queries = await db.execute(
        select(
            func.date(QueryLog.created_at).label("date"),
            func.count(QueryLog.id).label("queries"),
            func.avg(QueryLog.latency_ms).label("avg_latency"),
        )
        .where(QueryLog.created_at >= start_date)
        .group_by(func.date(QueryLog.created_at))
        .order_by("date")
    )

    return {
        "daily_usage": [
            {
                "date": str(row.date),
                "queries": row.queries,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
            }
            for row in daily_queries
        ],
        "period_days": days,
    }
