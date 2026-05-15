from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_type = Column(String(50), default="text")  # text | table | image | caption
    page_number = Column(Integer, nullable=True)
    chunk_metadata = Column(JSON, default={})
    vector_id = Column(String(255), nullable=True, index=True)  # ID in vector DB
    token_count = Column(Integer, nullable=True)
    embedding_model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")
