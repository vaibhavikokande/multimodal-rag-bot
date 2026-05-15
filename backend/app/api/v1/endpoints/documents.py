import os
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.crud.document import (
    create_document, get_document, get_documents_by_workspace,
    update_document_status, delete_document as crud_delete_document
)
from app.services.document_processor.processor import DocumentProcessor
from app.services.document_processor.chunker import DocumentChunker
from app.services.image_analyzer.analyzer import ImageAnalyzer
from app.services.embedding_pipeline.embedder import EmbeddingPipeline, VectorStore
from app.services.rag_engine.engine import RAGEngine
from app.crud.chunk import create_chunks
from loguru import logger

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    workspace_id: int = Form(...),
    tags: str = Form(""),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and queue documents for processing"""
    uploaded = []

    for file in files:
        # Validate extension
        ext = Path(file.filename).suffix.lower().strip(".")
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not supported"
            )

        # Validate size
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {size_mb:.1f}MB (max {settings.MAX_FILE_SIZE_MB}MB)"
            )

        # Save file
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / str(workspace_id) / unique_name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Determine document type
        doc_type = _get_doc_type(ext)

        # Create DB record
        doc = await create_document(
            db=db,
            title=file.filename,
            filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            file_type=ext,
            mime_type=file.content_type,
            doc_type=doc_type,
            workspace_id=workspace_id,
            uploaded_by_id=current_user.id,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
        )

        # Queue processing
        background_tasks.add_task(
            process_document_background,
            doc_id=doc.id,
            file_path=str(file_path),
            file_type=ext,
            workspace_id=workspace_id,
        )

        uploaded.append({
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "size": len(content),
        })

    return {"uploaded": uploaded, "count": len(uploaded)}


async def process_document_background(
    doc_id: int, file_path: str, file_type: str, workspace_id: int
):
    """Background task: process document, chunk, embed, store"""
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            await update_document_status(db, doc_id, DocumentStatus.processing)

            processor = DocumentProcessor()
            chunker = DocumentChunker()
            embedder = EmbeddingPipeline()
            vector_store = VectorStore()
            rag_engine = RAGEngine()

            # Process document
            result = await processor.process(file_path, file_type)

            # Chunk the content
            chunks = chunker.chunk(result["text"], file_type)

            # Add table chunks
            for table in result.get("tables", []):
                table_chunks = chunker.chunk_table(
                    table.get("content", ""),
                    page_number=table.get("page")
                )
                chunks.extend(table_chunks)

            # Add transcript chunks for video/audio
            if result.get("transcript"):
                transcript_chunks = chunker.chunk_transcript(result["transcript"])
                chunks.extend(transcript_chunks)

            # Re-index
            for i, chunk in enumerate(chunks):
                chunk["index"] = i

            # Generate embeddings
            chunks_with_embeddings = await embedder.embed_chunks(chunks)

            # Store in vector DB
            vector_ids = await vector_store.upsert_chunks(
                workspace_id=workspace_id,
                document_id=doc_id,
                chunks=chunks_with_embeddings,
            )

            # Save chunks to SQL DB
            await create_chunks(db, doc_id, chunks, vector_ids)

            # Generate summary and auto-tags
            summary = await rag_engine.generate_summary(
                result["text"][:8000]
            )
            auto_tags = await rag_engine.generate_auto_tags(result["text"])

            # Update document record
            from app.crud.document import finalize_document
            await finalize_document(
                db=db,
                doc_id=doc_id,
                status=DocumentStatus.indexed,
                chunk_count=len(chunks),
                page_count=result.get("page_count"),
                raw_text=result["text"][:50000],  # Store first 50k chars
                summary=summary,
                auto_tags=auto_tags,
                has_tables=result.get("has_tables", False),
                has_images=result.get("has_images", False),
                transcript=result.get("transcript"),
                processing_time=result.get("processing_time", 0),
            )

            logger.info(f"Document {doc_id} processed: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Document processing failed for {doc_id}: {e}")
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as err_db:
                await update_document_status(
                    err_db, doc_id, DocumentStatus.failed,
                    error=str(e)
                )


@router.get("/")
async def list_documents(
    workspace_id: int = Query(...),
    status: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    docs, total = await get_documents_by_workspace(
        db, workspace_id, status=status, doc_type=doc_type,
        search=search, page=page, per_page=per_page
    )
    return {
        "documents": [_doc_dict(d) for d in docs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{doc_id}")
async def get_document_detail(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_dict(doc, full=True)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector DB
    vector_store = VectorStore()
    await vector_store.delete_document(doc.workspace_id, doc_id)

    # Remove file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await crud_delete_document(db, doc_id)
    return {"message": "Document deleted successfully"}


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(doc.file_path, filename=doc.filename)


@router.post("/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    background_tasks.add_task(
        process_document_background,
        doc_id=doc_id,
        file_path=doc.file_path,
        file_type=doc.file_type,
        workspace_id=doc.workspace_id,
    )
    return {"message": "Reprocessing started", "doc_id": doc_id}


def _get_doc_type(ext: str) -> str:
    image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}
    video_exts = {"mp4", "avi", "mov", "mkv", "webm"}
    audio_exts = {"mp3", "wav", "m4a", "ogg", "flac"}
    if ext in image_exts:
        return "image"
    if ext in video_exts:
        return "video"
    if ext in audio_exts:
        return "audio"
    return ext


def _doc_dict(doc: Document, full: bool = False) -> dict:
    d = {
        "id": doc.id,
        "title": doc.title,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "doc_type": doc.doc_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "page_count": doc.page_count,
        "has_tables": doc.has_tables,
        "has_images": doc.has_images,
        "has_audio": doc.has_audio,
        "tags": doc.tags,
        "auto_tags": doc.auto_tags,
        "workspace_id": doc.workspace_id,
        "uploaded_by_id": doc.uploaded_by_id,
        "created_at": str(doc.created_at),
        "updated_at": str(doc.updated_at),
    }
    if full:
        d["summary"] = doc.summary
        d["doc_metadata"] = doc.doc_metadata
        d["language"] = doc.language
        d["processing_error"] = doc.processing_error
        d["processing_time"] = doc.processing_time
    return d
