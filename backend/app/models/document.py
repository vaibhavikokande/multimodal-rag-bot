from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    failed = "failed"


class DocumentType(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"
    pptx = "pptx"
    txt = "txt"
    csv = "csv"
    xlsx = "xlsx"
    image = "image"
    video = "video"
    audio = "audio"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_url = Column(String(1000), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(100), nullable=True)
    doc_type = Column(String(50), nullable=False)

    # Processing
    status = Column(String(50), default=DocumentStatus.pending)
    processing_error = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    chunk_count = Column(Integer, default=0)
    page_count = Column(Integer, nullable=True)

    # Content
    raw_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)

    # Metadata
    doc_metadata = Column(JSON, default={})
    tags = Column(JSON, default=[])
    auto_tags = Column(JSON, default=[])

    # Multimodal
    has_images = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_charts = Column(Boolean, default=False)
    has_audio = Column(Boolean, default=False)
    transcript = Column(Text, nullable=True)

    # Relations
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    workspace = relationship("Workspace", back_populates="documents")
    uploaded_by = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
