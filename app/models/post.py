import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    connected_account_id = Column(Integer, ForeignKey("connected_accounts.id"), nullable=True)
    platform = Column(Enum(Platform), nullable=False)
    post_type = Column(String(50))
    content_text = Column(Text)
    media_urls = Column(JSON)
    hashtags = Column(JSON)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    platform_post_id = Column(String(255))
    error_message = Column(Text)
    metadata_ = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
