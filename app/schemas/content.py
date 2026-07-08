from datetime import datetime
from pydantic import BaseModel
from app.models.post import Platform


class ContentIdeaRequest(BaseModel):
    platform: Platform
    niche: str
    count: int = 5


class ContentIdeaResponse(BaseModel):
    id: int
    platform: str
    topic: str
    content_type: str | None
    content_suggestion: str | None
    hashtags: str | None
    trend_source: str | None
    confidence_score: float | None
    used: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}


class RepurposeRequest(BaseModel):
    source_platform: Platform
    target_platform: Platform
    source_content: str


class RepurposeResponse(BaseModel):
    source_platform: str
    target_platform: str
    original_content: str
    adapted_content: str
    suggested_hashtags: list[str]
    notes: str


class OptimizeCaptionRequest(BaseModel):
    platform: Platform
    draft_caption: str


class OptimizeCaptionResponse(BaseModel):
    original: str
    optimized: str
    improvements: list[str]


class HashtagRequest(BaseModel):
    platform: Platform
    content: str
    count: int = 20


class HashtagResponse(BaseModel):
    hashtags: list[str]
    reasoning: str


class GenerateImageRequest(BaseModel):
    prompt: str
    style: str | None = None


class GenerateImageResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
    prompt: str
    style: str | None
    description: str | None


class GenerateVideoRequest(BaseModel):
    prompt: str
    style: str | None = None
    duration: int = 5  # seconds


class GenerateVideoResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
    prompt: str
    style: str | None
    duration: int
    description: str | None


class CreateContentRequest(BaseModel):
    platform: Platform
    topic: str
    content_type: str = "post"
    tone: str = "engaging"
    language: str = "English"


class CreateContentResponse(BaseModel):
    title: str
    caption: str
    hashtags: list[str]
    hook: str
    cta: str
    media_suggestion: str
    posting_tip: str


class ModifyContentRequest(BaseModel):
    platform: Platform
    original_content: str
    instruction: str = "improve engagement"


class ModifyContentResponse(BaseModel):
    modified_content: str
    hashtags: list[str]
    changes_made: list[str]
    engagement_score: float
