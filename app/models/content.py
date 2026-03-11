from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, func
from app.database import Base


class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)
    topic = Column(String(255), nullable=False)
    content_type = Column(String(50))  # image, carousel, reel, video
    content_suggestion = Column(Text)
    hashtags = Column(Text)
    trend_source = Column(String(255))
    confidence_score = Column(Float)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
