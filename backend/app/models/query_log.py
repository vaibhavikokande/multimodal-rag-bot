from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    query = Column(Text, nullable=False)
    response_preview = Column(Text, nullable=True)
    retrieved_doc_ids = Column(JSON, default=[])
    retrieval_scores = Column(JSON, default=[])
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="query_logs")
