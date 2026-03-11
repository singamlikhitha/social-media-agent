from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.post import Platform
from app.schemas.analytics import (
    PostAnalytics,
    MetricSnapshot,
    PlatformOverview,
    TopPost,
)
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/posts/{post_id}", response_model=PostAnalytics)
async def get_post_analytics(post_id: int, db: Session = Depends(get_db)):
    metrics = analytics_service.get_post_analytics(post_id, db)
    return PostAnalytics(
        post_id=post_id,
        platform=metrics[0].platform if metrics else "unknown",
        metrics=[MetricSnapshot.model_validate(m) for m in metrics],
    )


@router.get("/{platform}/overview", response_model=PlatformOverview)
async def get_platform_overview(
    platform: Platform,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    overview = analytics_service.get_platform_overview(platform.value, days, db)
    return overview


@router.post("/sync")
async def sync_analytics(db: Session = Depends(get_db)):
    synced = await analytics_service.sync_all_recent_posts(db)
    return {"synced_posts": synced, "message": f"Analytics synced for {synced} posts"}


@router.get("/{platform}/top-posts", response_model=list[TopPost])
async def get_top_posts(
    platform: Platform,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return analytics_service.get_top_posts(platform.value, db, limit)
