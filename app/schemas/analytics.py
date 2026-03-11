from datetime import datetime
from pydantic import BaseModel


class MetricSnapshot(BaseModel):
    metric_name: str
    metric_value: float
    recorded_at: datetime

    model_config = {"from_attributes": True}


class PostAnalytics(BaseModel):
    post_id: int
    platform: str
    metrics: list[MetricSnapshot]


class PlatformOverview(BaseModel):
    platform: str
    total_posts: int
    total_impressions: float
    total_reach: float
    total_likes: float
    total_comments: float
    avg_engagement_rate: float
    period_days: int


class OptimalTimeSlot(BaseModel):
    day_of_week: int
    hour: int
    avg_engagement: float
    sample_size: int


class TopPost(BaseModel):
    post_id: int
    content_text: str | None
    platform: str
    total_engagement: float
    published_at: datetime | None
