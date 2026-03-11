from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from app.database import Base


class EngagementMetric(Base):
    __tablename__ = "engagement_metrics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("scheduled_posts.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    metric_name = Column(String(50), nullable=False)  # impressions, reach, likes, comments, shares, saves, views
    metric_value = Column(Float, default=0)
    recorded_at = Column(DateTime, server_default=func.now())
