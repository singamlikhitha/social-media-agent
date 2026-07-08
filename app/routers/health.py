from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Social Media SaaS Platform", "version": "2.0.0"}


@router.get("/config")
async def config_status():
    return {
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "meta_configured": settings.meta_configured,
        "google_configured": settings.google_configured,
        "twitter_configured": settings.twitter_configured,
        "linkedin_configured": settings.linkedin_configured,
        "database": settings.DATABASE_URL.split("://")[0],
        "timezone": settings.TIMEZONE,
        "redis_configured": bool(settings.REDIS_URL),
    }


@router.get("/scheduler")
async def scheduler_status():
    from app.services.scheduler_service import scheduler_service
    return {
        "running": scheduler_service.scheduler.running,
        "pending_jobs": scheduler_service.get_pending_jobs(),
    }
