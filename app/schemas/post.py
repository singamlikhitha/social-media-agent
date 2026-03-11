from datetime import datetime
from pydantic import BaseModel
from app.models.post import Platform, PostStatus


class PostCreate(BaseModel):
    platform: Platform
    post_type: str = "image"
    content_text: str
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_time: datetime
    metadata: dict | None = None


class PostUpdate(BaseModel):
    content_text: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_time: datetime | None = None
    status: PostStatus | None = None


class PostResponse(BaseModel):
    id: int
    platform: Platform
    post_type: str | None
    content_text: str | None
    media_urls: list[str] | None
    hashtags: list[str] | None
    scheduled_time: datetime
    status: PostStatus
    platform_post_id: str | None
    error_message: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ScheduleRecommendation(BaseModel):
    platform: Platform
    recommended_times: list[dict]
    reasoning: str
