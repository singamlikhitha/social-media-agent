from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.post import ScheduledPost, PostStatus, Platform
from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.services.scheduler_service import scheduler_service
from app.services.posting_service import posting_service
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = ScheduledPost(
        platform=post.platform,
        post_type=post.post_type,
        content_text=post.content_text,
        media_urls=post.media_urls,
        hashtags=post.hashtags,
        scheduled_time=post.scheduled_time,
        status=PostStatus.SCHEDULED,
        metadata_=post.metadata,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    scheduler_service.schedule_post(db_post.id, db_post.scheduled_time)

    return db_post


@router.get("/", response_model=list[PostResponse])
async def list_posts(
    platform: Platform | None = None,
    status: PostStatus | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(ScheduledPost)

    if platform:
        query = query.filter(ScheduledPost.platform == platform)
    if status:
        query = query.filter(ScheduledPost.status == status)

    return (
        query.order_by(ScheduledPost.scheduled_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int, update: PostUpdate, db: Session = Depends(get_db)
):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    if "scheduled_time" in update_data and post.status == PostStatus.SCHEDULED:
        scheduler_service.reschedule_post(post_id, post.scheduled_time)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.SCHEDULED:
        scheduler_service.cancel_post(post_id)

    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}


@router.post("/{post_id}/publish-now")
async def publish_now(post_id: int, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Post already published")

    if post.status == PostStatus.SCHEDULED:
        scheduler_service.cancel_post(post_id)

    await posting_service.execute_post(post_id)

    db.refresh(post)
    return PostResponse.model_validate(post)


@router.get("/optimal-times/{platform}")
async def get_optimal_times(platform: Platform, db: Session = Depends(get_db)):
    times = analytics_service.get_optimal_times(platform.value, db)
    return {
        "platform": platform,
        "recommended_times": times,
        "reasoning": "Based on historical engagement data"
        if times and times[0]["sample_size"] > 0
        else "Default recommendations (no historical data yet)",
    }
