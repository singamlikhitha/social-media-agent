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
    GenerateImageRequest,
    GenerateImageResponse,
    GenerateVideoRequest,
    GenerateVideoResponse,
    CreateContentRequest,
    CreateContentResponse,
    ModifyContentRequest,
    ModifyContentResponse,
)
from app.services.content_service import content_service
from app.services.gemini_service import gemini_service
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/generate-ideas", response_model=list[ContentIdeaResponse])
async def generate_ideas(
    request: ContentIdeaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ideas = await content_service.generate_ideas(
        platform=request.platform.value,
        niche=request.niche,
        count=request.count,
        db=db,
        user_id=current_user.id,
    )
    return ideas


@router.get("/ideas", response_model=list[ContentIdeaResponse])
async def list_ideas(
    platform: str | None = None,
    unused_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return content_service.get_ideas(db, platform=platform, unused_only=unused_only, user_id=current_user.id)


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_content(
    request: RepurposeRequest,
    current_user: User = Depends(get_current_user),
):
    result = await content_service.repurpose_content(
        source_platform=request.source_platform.value,
        target_platform=request.target_platform.value,
        source_content=request.source_content,
    )
    return result


@router.post("/optimize-caption", response_model=OptimizeCaptionResponse)
async def optimize_caption(
    request: OptimizeCaptionRequest,
    current_user: User = Depends(get_current_user),
):
    result = await content_service.optimize_caption(
        platform=request.platform.value,
        draft_caption=request.draft_caption,
    )
    return result


@router.post("/suggest-hashtags", response_model=HashtagResponse)
async def suggest_hashtags(
    request: HashtagRequest,
    current_user: User = Depends(get_current_user),
):
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
    current_user: User = Depends(get_current_user),
):
    idea = (
        db.query(ContentIdea)
        .filter(ContentIdea.id == idea_id, ContentIdea.user_id == current_user.id)
        .first()
    )
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
        user_id=current_user.id,
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


@router.post("/create-content", response_model=CreateContentResponse)
async def create_content(
    request: CreateContentRequest,
    current_user: User = Depends(get_current_user),
):
    """Create ready-to-publish content from a topic using AI."""
    result = await content_service.create_content(
        platform=request.platform.value,
        topic=request.topic,
        content_type=request.content_type,
        tone=request.tone,
        language=request.language,
    )
    return result


@router.post("/modify-content", response_model=ModifyContentResponse)
async def modify_content(
    request: ModifyContentRequest,
    current_user: User = Depends(get_current_user),
):
    """Modify or rewrite user-provided content using AI."""
    result = await content_service.modify_content(
        platform=request.platform.value,
        original_content=request.original_content,
        instruction=request.instruction,
    )
    return result


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(
    request: GenerateImageRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an AI image using Gemini based on a text prompt."""
    try:
        result = await gemini_service.generate_image(
            prompt=request.prompt,
            user_id=current_user.id,
            style=request.style,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-video", response_model=GenerateVideoResponse)
async def generate_video(
    request: GenerateVideoRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an AI video from a text prompt."""
    try:
        result = await gemini_service.generate_video(
            prompt=request.prompt,
            user_id=current_user.id,
            duration=request.duration,
            style=request.style,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
