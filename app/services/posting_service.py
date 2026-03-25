import asyncio
import base64
import httpx
from pathlib import Path
from app.database import SessionLocal
from app.models.post import ScheduledPost, PostStatus, Platform
from app.config import settings
from app.utils.logger import logger

UPLOAD_DIR = Path("uploads")


class PostingService:
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative media URLs to absolute URLs for platform APIs."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        # Relative URL like /api/media/files/user_id/filename
        backend_base = settings.FRONTEND_URL.rstrip("/")
        return f"{backend_base}{url}"

    async def _get_public_url(self, url: str) -> str:
        """
        Get a publicly accessible URL for a media file.
        If it's a local file, upload to a free image host so platform APIs can access it.
        If it's already a public URL, return as-is.
        """
        if url.startswith("http://") and "localhost" not in url:
            return url
        if url.startswith("https://"):
            return url

        # Get local file path
        local_path = self._get_local_path(url)
        if not local_path:
            # If no local path, try making it an absolute URL (may work in production)
            return self._make_absolute_url(url)

        # Upload to imgbb (free, no key needed for anonymous uploads) or freeimage.host
        file_bytes = Path(local_path).read_bytes()
        b64_data = base64.b64encode(file_bytes).decode("utf-8")

        # Try freeimage.host (free, no API key required)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://freeimage.host/api/1/upload",
                    data={
                        "key": "6d207e02198a847aa98d0a2a901485a5",  # Public demo key
                        "action": "upload",
                        "source": b64_data,
                        "format": "json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    public_url = data.get("image", {}).get("url")
                    if public_url:
                        logger.info(f"Uploaded local file to freeimage.host: {public_url}")
                        return public_url
        except Exception as e:
            logger.warning(f"freeimage.host upload failed: {e}")

        # Fallback: try imgbb
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.imgbb.com/1/upload",
                    data={
                        "key": "a]",  # Will fail without valid key, but try
                        "image": b64_data,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    public_url = data.get("data", {}).get("url")
                    if public_url:
                        logger.info(f"Uploaded local file to imgbb: {public_url}")
                        return public_url
        except Exception as e:
            logger.warning(f"imgbb upload failed: {e}")

        # Last resort: return localhost URL (works only in production with public domain)
        logger.warning("Could not upload to public host, using local URL")
        return self._make_absolute_url(url)

    def _get_local_path(self, url: str) -> str | None:
        """Convert a media URL to a local file path (for YouTube uploads)."""
        # /api/media/files/{user_id}/{filename}
        if url.startswith("/api/media/files/"):
            parts = url.replace("/api/media/files/", "").split("/", 1)
            if len(parts) == 2:
                path = UPLOAD_DIR / parts[0] / parts[1]
                if path.exists():
                    return str(path.resolve())
        # Also try treating the URL itself as a local path
        p = Path(url)
        if p.exists():
            return str(p.resolve())
        return None

    async def execute_post(self, post_id: int):
        db = SessionLocal()
        try:
            post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
            if not post:
                logger.error(f"Post {post_id} not found")
                return

            if post.status == PostStatus.PUBLISHED:
                logger.warning(f"Post {post_id} already published")
                return

            post.status = PostStatus.PUBLISHING
            db.commit()

            try:
                # Auto-resolve connected_account_id if not set
                if not post.connected_account_id:
                    self._auto_resolve_account(post, db)

                if post.platform == Platform.INSTAGRAM:
                    platform_id = await self._publish_to_instagram(post, db)
                elif post.platform == Platform.YOUTUBE:
                    platform_id = self._publish_to_youtube(post, db)
                elif post.platform == Platform.FACEBOOK:
                    platform_id = await self._publish_to_facebook(post, db)
                elif post.platform == Platform.TWITTER:
                    platform_id = await self._publish_to_twitter(post, db)
                elif post.platform == Platform.LINKEDIN:
                    platform_id = await self._publish_to_linkedin(post, db)
                else:
                    raise ValueError(f"Unsupported platform: {post.platform}")

                post.platform_post_id = str(platform_id) if platform_id else None
                post.status = PostStatus.PUBLISHED
                post.error_message = None
                logger.info(f"Post {post_id} published successfully: {platform_id}")

            except Exception as e:
                post.status = PostStatus.FAILED
                post.error_message = str(e)
                logger.error(f"Post {post_id} publishing failed: {e}")

            db.commit()

        finally:
            db.close()

    def _auto_resolve_account(self, post: ScheduledPost, db):
        """Find the user's connected account for the post's platform."""
        from app.oauth.models import ConnectedAccount

        platform_map = {
            Platform.INSTAGRAM: "instagram",
            Platform.YOUTUBE: "youtube",
            Platform.FACEBOOK: "facebook",
            Platform.TWITTER: "twitter",
            Platform.LINKEDIN: "linkedin",
        }
        platform_str = platform_map.get(post.platform, post.platform.value)

        account = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.user_id == post.user_id,
                ConnectedAccount.platform == platform_str,
                ConnectedAccount.is_active == 1,
            )
            .first()
        )

        if account:
            post.connected_account_id = account.id
            db.commit()
            logger.info(f"Auto-resolved account {account.id} ({platform_str}) for post {post.id}")
        else:
            raise RuntimeError(
                f"No {platform_str} account connected. Please connect your {platform_str} account first."
            )

    def _get_credentials(self, post, db, platform: str) -> dict:
        from app.oauth.token_manager import get_platform_credentials
        creds = get_platform_credentials(post.user_id, platform, db)
        if not creds:
            raise RuntimeError(
                f"No {platform} account connected. Go to Accounts and connect your {platform} account."
            )
        return creds

    async def _publish_to_instagram(self, post: ScheduledPost, db) -> str:
        creds = self._get_credentials(post, db, "instagram")

        from app.services.instagram_service import InstagramService
        ig_service = InstagramService(
            access_token=creds["access_token"],
            account_id=creds["platform_user_id"],
        )

        # Instagram Graph API needs publicly accessible URLs
        raw_urls = post.media_urls or []
        media_urls = []
        for u in raw_urls:
            public_url = await self._get_public_url(u)
            media_urls.append(public_url)

        caption = post.content_text or ""

        if post.hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags)
            caption = f"{caption}\n\n{hashtag_str}"

        if post.post_type == "carousel" and len(media_urls) > 1:
            items = [{"url": url, "type": "IMAGE"} for url in media_urls]
            return await ig_service.create_carousel(items, caption)

        if not media_urls:
            raise ValueError("Instagram posts require at least one media URL")

        media_type = "REELS" if post.post_type == "reel" else "IMAGE"
        container_id = await ig_service.create_media_container(
            image_url=media_urls[0],
            caption=caption,
            media_type=media_type,
        )
        await ig_service.check_container_status(container_id)
        return await ig_service.publish_container(container_id)

    def _publish_to_youtube(self, post: ScheduledPost, db) -> str:
        creds = self._get_credentials(post, db, "youtube")

        from app.services.youtube_service import YouTubeService
        yt_creds = {
            "access_token": creds["access_token"],
            "refresh_token": creds.get("refresh_token"),
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
        }
        yt_service = YouTubeService(credentials=yt_creds)

        media_urls = post.media_urls or []
        if not media_urls:
            raise ValueError("YouTube posts require a video file")

        # YouTube needs local file path for upload
        local_path = self._get_local_path(media_urls[0])
        if not local_path:
            raise ValueError(
                "YouTube requires an uploaded video file. "
                "Please upload the video through the file uploader (not a URL)."
            )

        # Validate file is a video, not an image
        VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".wmv", ".flv", ".mkv", ".webm", ".m4v", ".3gp"}
        file_ext = Path(local_path).suffix.lower()
        if file_ext not in VIDEO_EXTENSIONS:
            raise ValueError(
                f"YouTube only supports video files (MP4, MOV, AVI, etc.). "
                f"You uploaded a '{file_ext}' file. Please upload a video instead."
            )

        metadata = post.metadata_ or {}
        return yt_service.upload_video(
            file_path=local_path,
            title=metadata.get("title", post.content_text[:100] if post.content_text else "Untitled"),
            description=post.content_text or "",
            tags=post.hashtags,
            category_id=metadata.get("category_id", "22"),
            privacy_status=metadata.get("privacy_status", "public"),
        )

    async def _publish_to_facebook(self, post: ScheduledPost, db) -> str:
        creds = self._get_credentials(post, db, "facebook")

        from app.services.facebook_service import FacebookService
        fb_service = FacebookService(
            access_token=creds["access_token"],
            page_id=creds["platform_user_id"],
        )

        caption = post.content_text or ""
        raw_urls = post.media_urls or []
        media_urls = []
        for u in raw_urls:
            public_url = await self._get_public_url(u)
            media_urls.append(public_url)

        if media_urls:
            return await fb_service.create_photo_post(media_urls[0], caption)
        else:
            return await fb_service.create_text_post(caption)

    async def _publish_to_twitter(self, post: ScheduledPost, db) -> str:
        creds = self._get_credentials(post, db, "twitter")

        from app.services.twitter_service import TwitterService
        twitter_service = TwitterService(access_token=creds["access_token"])

        caption = post.content_text or ""
        if post.hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags)
            caption = f"{caption}\n\n{hashtag_str}"

        raw_urls = post.media_urls or []
        media_urls = []
        for u in raw_urls:
            public_url = await self._get_public_url(u)
            media_urls.append(public_url)
        return await twitter_service.create_tweet(caption, media_urls=media_urls)

    async def _publish_to_linkedin(self, post: ScheduledPost, db) -> str:
        creds = self._get_credentials(post, db, "linkedin")

        from app.services.linkedin_service import LinkedInService
        li_service = LinkedInService(
            access_token=creds["access_token"],
            person_id=creds["platform_user_id"],
        )

        caption = post.content_text or ""
        raw_urls = post.media_urls or []
        media_urls = []
        for u in raw_urls:
            public_url = await self._get_public_url(u)
            media_urls.append(public_url)

        if media_urls:
            return await li_service.create_image_post(caption, media_urls[0])
        else:
            return await li_service.create_text_post(caption)


posting_service = PostingService()


def execute_post_job(post_id: int):
    """Entry point for scheduler jobs."""
    asyncio.run(posting_service.execute_post(post_id))


def sync_analytics_job():
    """Periodic analytics sync job."""
    from app.services.analytics_service import analytics_service

    db = SessionLocal()
    try:
        asyncio.run(analytics_service.sync_all_recent_posts(db))
    finally:
        db.close()
