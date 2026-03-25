import asyncio
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.post import ScheduledPost, PostStatus
from app.utils.logger import logger


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def publish_post(self, post_id: int):
    """Celery task to publish a scheduled post."""
    from app.services.posting_service import posting_service

    try:
        asyncio.run(posting_service.execute_post(post_id))
    except Exception as exc:
        logger.error(f"Publish task failed for post {post_id}: {exc}")
        raise self.retry(exc=exc)
