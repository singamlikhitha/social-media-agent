import asyncio
from app.celery_app import celery_app
from app.database import SessionLocal
from app.utils.logger import logger


@celery_app.task
def sync_all_analytics():
    """Periodic task to sync analytics for all users' recent posts."""
    from app.services.analytics_service import analytics_service

    db = SessionLocal()
    try:
        synced = asyncio.run(analytics_service.sync_all_recent_posts(db))
        logger.info(f"Analytics sync complete: {synced} posts synced")
        return {"synced": synced}
    finally:
        db.close()


@celery_app.task
def sync_user_analytics(user_id: str):
    """Sync analytics for a specific user's posts."""
    import uuid
    from app.services.analytics_service import analytics_service

    db = SessionLocal()
    try:
        uid = uuid.UUID(user_id)
        synced = asyncio.run(analytics_service.sync_all_recent_posts(db, user_id=uid))
        logger.info(f"Analytics sync for user {user_id}: {synced} posts synced")
        return {"synced": synced, "user_id": user_id}
    finally:
        db.close()
