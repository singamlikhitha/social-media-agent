from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.post import ScheduledPost, PostStatus, Platform
from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.services.scheduler_service import scheduler_service
from app.services.posting_service import posting_service
from app.services.analytics_service import analytics_service
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=201)
@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-resolve connected account if not provided
    connected_account_id = post.connected_account_id
    if not connected_account_id:
        from app.oauth.models import ConnectedAccount
        account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == current_user.id,
                ConnectedAccount.platform == post.platform.value,
                ConnectedAccount.is_active == 1,
            )
            .first()
        )
        if not account:
            raise HTTPException(
                status_code=400,
                detail=f"No {post.platform.value} account connected. Please connect your {post.platform.value} account first in the Accounts page.",
            )
        connected_account_id = account.id

    db_post = ScheduledPost(
        user_id=current_user.id,
        platform=post.platform,
        post_type=post.post_type,
        content_text=post.content_text,
        media_urls=post.media_urls,
        hashtags=post.hashtags,
        scheduled_time=post.scheduled_time,
        status=PostStatus.SCHEDULED,
        connected_account_id=connected_account_id,
        metadata_=post.metadata,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    scheduler_service.schedule_post(db_post.id, db_post.scheduled_time)

    return db_post


@router.get("", response_model=list[PostResponse])
@router.get("/", response_model=list[PostResponse])
async def list_posts(
    platform: Platform | None = None,
    status: PostStatus | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user.id)

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
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(ScheduledPost)
        .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    update: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(ScheduledPost)
        .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
        .first()
    )
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
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(ScheduledPost)
        .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.status == PostStatus.SCHEDULED:
        scheduler_service.cancel_post(post_id)

    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}


@router.post("/{post_id}/publish-now")
async def publish_now(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(ScheduledPost)
        .filter(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
        .first()
    )
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
async def get_optimal_times(
    platform: Platform,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    times = analytics_service.get_optimal_times(platform.value, db, user_id=current_user.id)
    return {
        "platform": platform,
        "recommended_times": times,
        "reasoning": "Based on historical engagement data"
        if times and times[0]["sample_size"] > 0
        else "Default recommendations (no historical data yet)",
    }
