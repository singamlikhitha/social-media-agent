from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.content import ContentIdea
from app.models.post import ScheduledPost, PostStatus
from app.schemas.content import (
    ContentIdeaRequest,
    ContentIdeaResponse,
    RepurposeRequest,
    RepurposeResponse,
    OptimizeCaptionRequest,
    OptimizeCaptionResponse,
    HashtagRequest,
    HashtagResponse,
)
from app.services.content_service import content_service

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/generate-ideas", response_model=list[ContentIdeaResponse])
async def generate_ideas(
    request: ContentIdeaRequest, db: Session = Depends(get_db)
):
    ideas = await content_service.generate_ideas(
        platform=request.platform.value,
        niche=request.niche,
        count=request.count,
        db=db,
    )
    return ideas


@router.get("/ideas", response_model=list[ContentIdeaResponse])
async def list_ideas(
    platform: str | None = None,
    unused_only: bool = False,
    db: Session = Depends(get_db),
):
    return content_service.get_ideas(db, platform=platform, unused_only=unused_only)


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_content(request: RepurposeRequest):
    result = await content_service.repurpose_content(
        source_platform=request.source_platform.value,
        target_platform=request.target_platform.value,
        source_content=request.source_content,
    )
    return result


@router.post("/optimize-caption", response_model=OptimizeCaptionResponse)
async def optimize_caption(request: OptimizeCaptionRequest):
    result = await content_service.optimize_caption(
        platform=request.platform.value,
        draft_caption=request.draft_caption,
    )
    return result


@router.post("/suggest-hashtags", response_model=HashtagResponse)
async def suggest_hashtags(request: HashtagRequest):
    result = await content_service.suggest_hashtags(
        platform=request.platform.value,
        content=request.content,
        count=request.count,
    )
    return result


@router.post("/ideas/{idea_id}/create-post")
async def create_post_from_idea(
    idea_id: int,
    scheduled_time: str = Query(..., description="ISO format datetime"),
    db: Session = Depends(get_db),
):
    idea = db.query(ContentIdea).filter(ContentIdea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Content idea not found")

    from datetime import datetime

    try:
        schedule_dt = datetime.fromisoformat(scheduled_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    import json

    hashtags = None
    if idea.hashtags:
        try:
            hashtags = json.loads(idea.hashtags)
        except json.JSONDecodeError:
            hashtags = [h.strip() for h in idea.hashtags.split(",") if h.strip()]

    post = ScheduledPost(
        platform=idea.platform,
        post_type=idea.content_type or "image",
        content_text=idea.content_suggestion,
        hashtags=hashtags,
        scheduled_time=schedule_dt,
        status=PostStatus.DRAFT,
    )
    db.add(post)

    idea.used = True
    db.commit()
    db.refresh(post)

    return {
        "post_id": post.id,
        "message": "Post created from idea. Set status to 'scheduled' and add media to publish.",
    }
