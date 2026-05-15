from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from app.models.document import Document, DocumentStatus


async def create_document(db: AsyncSession, **kwargs) -> Document:
    doc = Document(**kwargs)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def get_document(db: AsyncSession, doc_id: int) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def get_documents_by_workspace(
    db: AsyncSession, workspace_id: int,
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1, per_page: int = 20
) -> Tuple[List[Document], int]:
    query = select(Document).where(Document.workspace_id == workspace_id)

    if status:
        query = query.where(Document.status == status)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if search:
        query = query.where(
            or_(
                Document.title.ilike(f"%{search}%"),
                Document.filename.ilike(f"%{search}%"),
            )
        )

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return result.scalars().all(), total or 0


async def update_document_status(
    db: AsyncSession, doc_id: int, status: DocumentStatus, error: str = None
):
    values = {"status": status}
    if error:
        values["processing_error"] = error
    await db.execute(update(Document).where(Document.id == doc_id).values(**values))
    await db.commit()


async def finalize_document(db: AsyncSession, doc_id: int, **kwargs):
    await db.execute(update(Document).where(Document.id == doc_id).values(**kwargs))
    await db.commit()


async def delete_document(db: AsyncSession, doc_id: int):
    await db.execute(delete(Document).where(Document.id == doc_id))
    await db.commit()
