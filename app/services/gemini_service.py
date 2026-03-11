import json
from google import genai
from app.config import settings
from app.utils.logger import logger


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    async def generate_content_ideas(
        self, platform: str, niche: str, count: int = 5
    ) -> list[dict]:
        prompt = f"""You are a social media content strategist.
Generate {count} content ideas for {platform} in the "{niche}" niche.

For each idea provide:
- topic: a concise topic title
- content_type: the post format ({self._get_content_types(platform)})
- caption: a ready-to-use caption with emojis and hooks
- hashtags: list of 10-20 relevant hashtags (without #)
- reasoning: why this idea would perform well right now

Focus on trending topics, seasonal relevance, and high-engagement formats."""

        response_schema = {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "topic": {"type": "STRING"},
                    "content_type": {"type": "STRING"},
                    "caption": {"type": "STRING"},
                    "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "reasoning": {"type": "STRING"},
                },
                "required": ["topic", "content_type", "caption", "hashtags", "reasoning"],
            },
        }

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini content generation failed: {e}")
            raise

    async def analyze_trends(self, niche: str) -> list[dict]:
        prompt = f"""Analyze current trending topics in the "{niche}" niche for social media.

For each trend provide:
- trend: the trending topic or theme
- description: brief explanation of why it's trending
- platforms: which platforms it's most relevant for (instagram, youtube)
- content_angles: 2-3 suggested content angles to leverage this trend
- urgency: how time-sensitive this trend is (high, medium, low)"""

        response_schema = {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "trend": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "platforms": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "content_angles": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "urgency": {"type": "STRING"},
                },
                "required": ["trend", "description", "platforms", "content_angles", "urgency"],
            },
        }

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini trend analysis failed: {e}")
            raise

    async def repurpose_content(
        self, source_platform: str, target_platform: str, content: str
    ) -> dict:
        platform_guidelines = {
            "instagram": "Max 2200 chars for caption. Use emojis, line breaks, and a strong hook in the first line. Place hashtags at the end (max 30). Include a CTA.",
            "youtube": "Title max 100 chars (hook-driven). Description max 5000 chars with timestamps, links section, and tags. Tags total max 500 chars.",
        }

        prompt = f"""You are a content repurposing expert.

Adapt this {source_platform} content for {target_platform}:

--- ORIGINAL CONTENT ---
{content}
--- END ---

Target platform guidelines: {platform_guidelines.get(target_platform, '')}

Provide:
- adapted_content: the fully adapted content ready to post
- suggested_hashtags: relevant hashtags for the target platform (without #)
- notes: key changes made and why"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "adapted_content": {"type": "STRING"},
                "suggested_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "notes": {"type": "STRING"},
            },
            "required": ["adapted_content", "suggested_hashtags", "notes"],
        }

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini content repurposing failed: {e}")
            raise

    async def optimize_caption(self, platform: str, draft_caption: str) -> dict:
        prompt = f"""You are a social media copywriting expert.

Optimize this {platform} caption for maximum engagement:

--- DRAFT ---
{draft_caption}
--- END ---

Provide:
- optimized: the improved caption
- improvements: list of specific changes made and why"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "optimized": {"type": "STRING"},
                "improvements": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": ["optimized", "improvements"],
        }

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini caption optimization failed: {e}")
            raise

    async def suggest_hashtags(
        self, platform: str, content: str, count: int = 20
    ) -> dict:
        max_tags = min(count, 30) if platform == "instagram" else count

        prompt = f"""Suggest {max_tags} hashtags for this {platform} content:

--- CONTENT ---
{content}
--- END ---

Provide a mix of:
- High-volume hashtags (broad reach)
- Medium-volume hashtags (moderate competition)
- Niche-specific hashtags (targeted audience)

Return hashtags without the # symbol.
Provide:
- hashtags: ordered list from most to least relevant
- reasoning: brief strategy explanation"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "reasoning": {"type": "STRING"},
            },
            "required": ["hashtags", "reasoning"],
        }

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini hashtag suggestion failed: {e}")
            raise

    def _get_content_types(self, platform: str) -> str:
        types = {
            "instagram": "image, carousel, reel, story",
            "youtube": "video, short",
        }
        return types.get(platform, "post")


gemini_service = GeminiService()
