from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import DocumentChunk


async def create_chunks(
    db: AsyncSession, doc_id: int, chunks: List[dict], vector_ids: List[str]
):
    db_chunks = []
    for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
        db_chunk = DocumentChunk(
            document_id=doc_id,
            chunk_index=chunk.get("index", i),
            content=chunk["content"],
            chunk_type=chunk.get("metadata", {}).get("chunk_type", "text"),
            page_number=chunk.get("metadata", {}).get("page_number"),
            chunk_metadata=chunk.get("metadata", {}),
            vector_id=vector_id,
            token_count=chunk.get("metadata", {}).get("token_count"),
        )
        db_chunks.append(db_chunk)

    db.add_all(db_chunks)
    await db.commit()
    return db_chunks
