import base64
import json
import uuid
from pathlib import Path

from google import genai
from google.genai import types

from app.config import settings
from app.utils.logger import logger

UPLOAD_DIR = Path("uploads")


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
            "facebook": "Max 63,206 chars. Engaging opening, can include links. More conversational tone.",
            "twitter": "Max 280 chars per tweet. Concise, punchy. Can create threads for longer content.",
            "linkedin": "Max 3000 chars. Professional tone. Use line breaks for readability. Storytelling format works well.",
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

    async def generate_image(self, prompt: str, user_id: int, style: str | None = None) -> dict:
        """Generate an image using Together.ai, Pollinations.ai, or Unsplash fallback."""
        import httpx

        full_prompt = prompt
        if style:
            full_prompt += f", {style} style"

        image_bytes = None
        content_type = "image/jpeg"
        source = None

        # Method 1: Together.ai (free tier, reliable)
        if settings.TOGETHER_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        "https://api.together.xyz/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "black-forest-labs/FLUX.1-schnell-Free",
                            "prompt": full_prompt,
                            "width": 1024,
                            "height": 1024,
                            "n": 1,
                            "steps": 4,
                            "response_format": "b64_json",
                        },
                    )
                    if response.status_code == 200:
                        data = response.json()
                        b64_data = data["data"][0]["b64_json"]
                        image_bytes = base64.b64decode(b64_data)
                        content_type = "image/png"
                        source = "together-flux"
            except Exception as e:
                logger.warning(f"Together.ai error: {e}")

        # Method 2: Pollinations.ai (free, no key)
        if not image_bytes:
            import re
            import random
            from urllib.parse import quote

            clean_prompt = re.sub(r'[^\w\s\-]', ' ', full_prompt).strip()
            clean_prompt = re.sub(r'\s+', ' ', clean_prompt)

            try:
                seed = random.randint(1, 99999)
                encoded = quote(clean_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
                async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
                    response = await client.get(url)
                if response.status_code == 200 and len(response.content) > 1000:
                    image_bytes = response.content
                    content_type = response.headers.get("content-type", "image/jpeg")
                    source = "pollinations"
            except Exception as e:
                logger.warning(f"Pollinations error: {e}")

        # Method 3: LoremFlickr (free stock photos matching keywords)
        if not image_bytes:
            try:
                import re as _re
                # Extract simple keywords from prompt directly
                words = _re.sub(r'[^\w\s]', ' ', prompt.lower()).split()
                stop_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'is', 'are', 'and', 'or', 'that', 'this', 'it', 'i', 'want', 'need', 'create', 'generate', 'make', 'image', 'photo', 'picture', 'style'}
                keywords = [w for w in words if w not in stop_words and len(w) > 2][:3]
                keyword_str = ",".join(keywords) if keywords else "nature"

                search_url = f"https://loremflickr.com/1024/1024/{keyword_str}"
                logger.info(f"LoremFlickr URL: {search_url}")
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    response = await client.get(search_url)
                if response.status_code == 200 and len(response.content) > 1000:
                    image_bytes = response.content
                    content_type = response.headers.get("content-type", "image/jpeg")
                    source = "flickr"
                else:
                    logger.warning(f"LoremFlickr: status {response.status_code}, size {len(response.content)}")
            except Exception as e:
                logger.warning(f"LoremFlickr fallback error: {e}")

        if not image_bytes:
            raise ValueError(
                "Image generation is temporarily unavailable. "
                "For reliable AI image generation, add TOGETHER_API_KEY to .env "
                "(get one free at https://api.together.xyz)"
            )

        ext = ".jpg" if "jpeg" in content_type else ".png"
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = user_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        media_url = f"/api/media/files/{user_id}/{unique_name}"

        return {
            "url": media_url,
            "filename": unique_name,
            "size": len(image_bytes),
            "content_type": content_type,
            "prompt": prompt,
            "style": style,
            "description": f"Image sourced via {source}: {full_prompt}",
        }

    async def generate_video(self, prompt: str, user_id: int, duration: int = 5, style: str | None = None) -> dict:
        """Generate an AI video using multiple fallback methods."""
        import httpx
        import asyncio

        full_prompt = prompt
        if style:
            full_prompt += f", {style} style"

        video_bytes = None
        source = None

        # Method 1: Google Veo via Gemini API
        try:
            from google.genai import types as genai_types

            logger.info(f"Attempting Veo video generation: {full_prompt[:80]}...")
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=full_prompt,
                config=genai_types.GenerateVideosConfig(
                    person_generation="allow_all",
                    aspect_ratio="16:9",
                    number_of_videos=1,
                ),
            )

            # Poll for completion (max 5 minutes)
            max_wait = 300
            waited = 0
            while not operation.done and waited < max_wait:
                await asyncio.sleep(10)
                waited += 10
                operation = self.client.models.get_operation(operation)
                logger.info(f"Veo generation: waiting... ({waited}s)")

            if operation.done and operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0]
                video_data = self.client.files.download(file=video.video)
                if hasattr(video_data, '__iter__') and not isinstance(video_data, bytes):
                    chunks = []
                    for chunk in video_data:
                        chunks.append(chunk)
                    video_bytes = b"".join(chunks)
                else:
                    video_bytes = video_data
                source = "veo-2"
                logger.info("Veo video generated successfully")
            else:
                logger.warning("Veo generation timed out or returned no result")
                video_bytes = None
        except Exception as e:
            logger.warning(f"Veo video generation failed: {e}")
            video_bytes = None

        # Method 2: Replicate API (if token configured)
        if not video_bytes and settings.REPLICATE_API_TOKEN:
            try:
                logger.info("Attempting Replicate video generation...")
                async with httpx.AsyncClient(timeout=300) as client:
                    resp = await client.post(
                        "https://api.replicate.com/v1/predictions",
                        headers={
                            "Authorization": f"Bearer {settings.REPLICATE_API_TOKEN}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "version": "b697e06acde237e32ff5a48b7e98eac2dbfaa06e76ee66a349060f5df678e67f",
                            "input": {"prompt": full_prompt, "num_frames": 25 * duration},
                        },
                    )
                    if resp.status_code in (200, 201):
                        prediction = resp.json()
                        prediction_id = prediction["id"]
                        max_wait, waited = 300, 0
                        while waited < max_wait:
                            await asyncio.sleep(5)
                            waited += 5
                            poll_resp = await client.get(
                                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                                headers={"Authorization": f"Bearer {settings.REPLICATE_API_TOKEN}"},
                            )
                            status_data = poll_resp.json()
                            if status_data.get("status") == "succeeded":
                                output = status_data.get("output")
                                video_url = output if isinstance(output, str) else output[0] if isinstance(output, list) else None
                                if video_url:
                                    dl_resp = await client.get(video_url)
                                    if dl_resp.status_code == 200:
                                        video_bytes = dl_resp.content
                                        source = "replicate"
                                break
                            elif status_data.get("status") == "failed":
                                logger.warning(f"Replicate failed: {status_data.get('error')}")
                                break
            except Exception as e:
                logger.warning(f"Replicate video generation failed: {e}")

        # Method 3: HuggingFace Inference API (free, no key needed)
        if not video_bytes:
            hf_models = [
                "ali-vilab/text-to-video-ms-1.7b",
                "damo-vilab/text-to-video-ms-1.7b",
            ]
            for model_id in hf_models:
                try:
                    logger.info(f"Attempting HuggingFace video generation with {model_id}...")
                    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                        resp = await client.post(
                            f"https://api-inference.huggingface.co/models/{model_id}",
                            json={"inputs": full_prompt},
                            headers={"Content-Type": "application/json"},
                        )
                        if resp.status_code == 200 and len(resp.content) > 10000:
                            ct = resp.headers.get("content-type", "")
                            if "video" in ct or "octet" in ct or len(resp.content) > 50000:
                                video_bytes = resp.content
                                source = f"huggingface-{model_id.split('/')[-1]}"
                                logger.info(f"HuggingFace video generated via {model_id}")
                                break
                        elif resp.status_code == 503:
                            # Model is loading, wait and retry once
                            logger.info(f"HuggingFace model {model_id} loading, waiting 30s...")
                            await asyncio.sleep(30)
                            resp = await client.post(
                                f"https://api-inference.huggingface.co/models/{model_id}",
                                json={"inputs": full_prompt},
                                headers={"Content-Type": "application/json"},
                            )
                            if resp.status_code == 200 and len(resp.content) > 10000:
                                video_bytes = resp.content
                                source = f"huggingface-{model_id.split('/')[-1]}"
                                break
                        else:
                            logger.warning(f"HuggingFace {model_id}: status {resp.status_code}")
                except Exception as e:
                    logger.warning(f"HuggingFace {model_id} failed: {e}")

        # Method 4: Generate video from AI image + ffmpeg (create slideshow video)
        if not video_bytes:
            try:
                logger.info("Falling back to AI image → video conversion...")
                import subprocess
                import tempfile

                # Generate an AI image first
                image_result = await self.generate_image(prompt=prompt, user_id=user_id, style=style)
                image_path = UPLOAD_DIR / str(user_id) / image_result["filename"]

                if image_path.exists():
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                        tmp_path = tmp.name

                    # Use ffmpeg to create a video from the image (zoom/pan effect)
                    cmd = [
                        "ffmpeg", "-y",
                        "-loop", "1",
                        "-i", str(image_path),
                        "-vf", f"zoompan=z='min(zoom+0.0015,1.5)':d={duration*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720,format=yuv420p",
                        "-t", str(duration),
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        tmp_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, timeout=60)

                    if result.returncode == 0 and Path(tmp_path).exists():
                        video_bytes = Path(tmp_path).read_bytes()
                        source = "image-to-video"
                        logger.info("Created video from AI-generated image with zoom effect")
                    else:
                        # Simple ffmpeg without zoom (simpler filter)
                        cmd_simple = [
                            "ffmpeg", "-y",
                            "-loop", "1",
                            "-i", str(image_path),
                            "-t", str(duration),
                            "-c:v", "libx264",
                            "-vf", "scale=1280:720,format=yuv420p",
                            "-pix_fmt", "yuv420p",
                            tmp_path,
                        ]
                        result = subprocess.run(cmd_simple, capture_output=True, timeout=60)
                        if result.returncode == 0 and Path(tmp_path).exists():
                            video_bytes = Path(tmp_path).read_bytes()
                            source = "image-to-video-simple"

                    # Cleanup temp file
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Image-to-video fallback failed: {e}")

        if not video_bytes:
            raise ValueError(
                "Video generation is currently unavailable. For reliable video generation, "
                "add REPLICATE_API_TOKEN to your environment (get one free at https://replicate.com)."
            )

        # Save video file
        user_dir = UPLOAD_DIR / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}.mp4"
        file_path = user_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(video_bytes)

        media_url = f"/api/media/files/{user_id}/{unique_name}"

        return {
            "url": media_url,
            "filename": unique_name,
            "size": len(video_bytes),
            "content_type": "video/mp4",
            "prompt": prompt,
            "style": style,
            "duration": duration,
            "description": f"AI video generated via {source}: {full_prompt}",
        }

    async def create_content(
        self, platform: str, topic: str, content_type: str = "post",
        tone: str = "engaging", language: str = "English"
    ) -> dict:
        """Generate ready-to-publish content from a topic."""
        platform_guidelines = {
            "instagram": "Max 2200 chars caption. Strong hook in first line, emojis, line breaks, CTA at end. Place hashtags at end (max 30).",
            "youtube": "Title max 100 chars (hook-driven). Description max 5000 chars with timestamps. Tags total max 500 chars.",
            "facebook": "Max 63,206 chars. Engaging opening, conversational tone, can include links.",
            "twitter": "Max 280 chars. Concise, punchy, attention-grabbing. Use threads for longer content.",
            "linkedin": "Max 3000 chars. Professional tone, line breaks for readability, storytelling format.",
        }

        prompt = f"""You are an expert social media content creator.

Create a complete, ready-to-publish {content_type} for {platform} about the topic: "{topic}"

Platform guidelines: {platform_guidelines.get(platform, '')}
Tone: {tone}
Language: {language}

Provide:
- title: A compelling title/headline for the content
- caption: The full ready-to-post caption/text (platform-optimized, with emojis and formatting)
- hashtags: List of 15-25 relevant hashtags (without #, mix of high/medium/niche volume)
- hook: The attention-grabbing opening line
- cta: A call-to-action to include
- media_suggestion: What type of image/video would best accompany this post
- posting_tip: One tip for maximizing engagement with this specific content"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "caption": {"type": "STRING"},
                "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "hook": {"type": "STRING"},
                "cta": {"type": "STRING"},
                "media_suggestion": {"type": "STRING"},
                "posting_tip": {"type": "STRING"},
            },
            "required": ["title", "caption", "hashtags", "hook", "cta", "media_suggestion", "posting_tip"],
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
            logger.error(f"Gemini content creation failed: {e}")
            raise

    async def modify_content(
        self, platform: str, original_content: str,
        instruction: str = "improve engagement"
    ) -> dict:
        """Modify/rewrite user-provided content based on instructions."""
        prompt = f"""You are an expert social media content editor.

The user has provided content for {platform} and wants you to modify it.

--- ORIGINAL CONTENT ---
{original_content}
--- END ---

Modification instruction: {instruction}

Provide:
- modified_content: The fully rewritten/modified content ready to post
- hashtags: List of 15-25 relevant hashtags (without #)
- changes_made: List of specific changes and why each improves the content
- engagement_score: Estimated engagement improvement (1-10 scale)"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "modified_content": {"type": "STRING"},
                "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
                "changes_made": {"type": "ARRAY", "items": {"type": "STRING"}},
                "engagement_score": {"type": "NUMBER"},
            },
            "required": ["modified_content", "hashtags", "changes_made", "engagement_score"],
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
            logger.error(f"Gemini content modification failed: {e}")
            raise

    def _get_content_types(self, platform: str) -> str:
        types = {
            "instagram": "image, carousel, reel, story",
            "youtube": "video, short",
            "facebook": "text, image, video, link",
            "twitter": "tweet, thread",
            "linkedin": "text, image, article",
        }
        return types.get(platform, "post")


gemini_service = GeminiService()
