import asyncio
from app.database import SessionLocal
from app.models.post import ScheduledPost, PostStatus, Platform
from app.services.instagram_service import instagram_service
from app.services.youtube_service import youtube_service
from app.utils.logger import logger


class PostingService:
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
                if post.platform == Platform.INSTAGRAM:
                    platform_id = await self._publish_to_instagram(post)
                elif post.platform == Platform.YOUTUBE:
                    platform_id = self._publish_to_youtube(post)
                else:
                    raise ValueError(f"Unsupported platform: {post.platform}")

                post.platform_post_id = platform_id
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

    async def _publish_to_instagram(self, post: ScheduledPost) -> str:
        media_urls = post.media_urls or []
        caption = post.content_text or ""

        if post.hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in post.hashtags)
            caption = f"{caption}\n\n{hashtag_str}"

        if post.post_type == "carousel" and len(media_urls) > 1:
            items = [{"url": url, "type": "IMAGE"} for url in media_urls]
            return await instagram_service.create_carousel(items, caption)

        if not media_urls:
            raise ValueError("Instagram posts require at least one media URL")

        media_type = "REELS" if post.post_type == "reel" else "IMAGE"
        container_id = await instagram_service.create_media_container(
            image_url=media_urls[0],
            caption=caption,
            media_type=media_type,
        )
        await instagram_service.check_container_status(container_id)
        return await instagram_service.publish_container(container_id)

    def _publish_to_youtube(self, post: ScheduledPost) -> str:
        media_urls = post.media_urls or []
        if not media_urls:
            raise ValueError("YouTube posts require a video file path")

        metadata = post.metadata_ or {}
        return youtube_service.upload_video(
            file_path=media_urls[0],
            title=metadata.get("title", post.content_text[:100] if post.content_text else "Untitled"),
            description=post.content_text or "",
            tags=post.hashtags,
            category_id=metadata.get("category_id", "22"),
            privacy_status=metadata.get("privacy_status", "private"),
        )


posting_service = PostingService()


def execute_post_job(post_id: int):
    """Entry point for APScheduler jobs (runs in thread pool)."""
    asyncio.run(posting_service.execute_post(post_id))


def sync_analytics_job():
    """Periodic analytics sync job."""
    from app.services.analytics_service import analytics_service

    db = SessionLocal()
    try:
        asyncio.run(analytics_service.sync_all_recent_posts(db))
    finally:
        db.close()
