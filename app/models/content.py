import uuid
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    topic = Column(String(255), nullable=False)
    content_type = Column(String(50))
    content_suggestion = Column(Text)
    hashtags = Column(Text)
    trend_source = Column(Text)
    confidence_score = Column(Float)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
