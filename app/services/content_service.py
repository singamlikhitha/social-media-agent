import json
import uuid
from sqlalchemy.orm import Session
from app.models.content import ContentIdea
from app.services.gemini_service import gemini_service
from app.utils.logger import logger


class ContentService:
    async def generate_ideas(
        self, platform: str, niche: str, count: int, db: Session, user_id: uuid.UUID | None = None
    ) -> list[ContentIdea]:
        ideas_data = await gemini_service.generate_content_ideas(platform, niche, count)

        ideas = []
        for item in ideas_data:
            idea = ContentIdea(
                user_id=user_id,
                platform=platform,
                topic=item["topic"],
                content_type=item.get("content_type"),
                content_suggestion=item.get("caption", ""),
                hashtags=json.dumps(item.get("hashtags", [])),
                trend_source=item.get("reasoning", ""),
                confidence_score=0.8,
                used=False,
            )
            db.add(idea)
            ideas.append(idea)

        db.commit()
        for idea in ideas:
            db.refresh(idea)

        logger.info(f"Generated {len(ideas)} content ideas for {platform}/{niche}")
        return ideas

    async def repurpose_content(
        self,
        source_platform: str,
        target_platform: str,
        source_content: str,
    ) -> dict:
        result = await gemini_service.repurpose_content(
            source_platform, target_platform, source_content
        )

        logger.info(f"Repurposed content from {source_platform} to {target_platform}")
        return {
            "source_platform": source_platform,
            "target_platform": target_platform,
            "original_content": source_content,
            "adapted_content": result["adapted_content"],
            "suggested_hashtags": result.get("suggested_hashtags", []),
            "notes": result.get("notes", ""),
        }

    async def optimize_caption(self, platform: str, draft_caption: str) -> dict:
        result = await gemini_service.optimize_caption(platform, draft_caption)

        return {
            "original": draft_caption,
            "optimized": result["optimized"],
            "improvements": result.get("improvements", []),
        }

    async def suggest_hashtags(
        self, platform: str, content: str, count: int
    ) -> dict:
        result = await gemini_service.suggest_hashtags(platform, content, count)

        return {
            "hashtags": result["hashtags"],
            "reasoning": result.get("reasoning", ""),
        }

    def get_ideas(
        self, db: Session, platform: str | None = None, unused_only: bool = False, user_id: uuid.UUID | None = None
    ) -> list[ContentIdea]:
        query = db.query(ContentIdea)

        if user_id:
            query = query.filter(ContentIdea.user_id == user_id)
        if platform:
            query = query.filter(ContentIdea.platform == platform)
        if unused_only:
            query = query.filter(ContentIdea.used == False)

        return query.order_by(ContentIdea.created_at.desc()).all()

    async def create_content(
        self, platform: str, topic: str, content_type: str = "post",
        tone: str = "engaging", language: str = "English"
    ) -> dict:
        result = await gemini_service.create_content(
            platform=platform, topic=topic, content_type=content_type,
            tone=tone, language=language
        )
        logger.info(f"Created content for {platform} on topic: {topic}")
        return result

    async def modify_content(
        self, platform: str, original_content: str, instruction: str = "improve engagement"
    ) -> dict:
        result = await gemini_service.modify_content(
            platform=platform, original_content=original_content, instruction=instruction
        )
        logger.info(f"Modified content for {platform}")
        return result

    def mark_idea_used(self, db: Session, idea_id: int) -> ContentIdea | None:
        idea = db.query(ContentIdea).filter(ContentIdea.id == idea_id).first()
        if idea:
            idea.used = True
            db.commit()
            db.refresh(idea)
        return idea


content_service = ContentService()
