from fastapi import APIRouter
from app.config import settings
from app.services.scheduler_service import scheduler_service

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "Social Media Content Scheduler"}


@router.get("/config")
async def config_status():
    return {
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "instagram_configured": settings.instagram_configured,
        "youtube_configured": settings.youtube_configured,
        "database_url": settings.DATABASE_URL.split("///")[0] + "///***",
        "timezone": settings.TIMEZONE,
    }


@router.get("/scheduler")
async def scheduler_status():
    return {
        "running": scheduler_service.scheduler.running,
        "pending_jobs": scheduler_service.get_pending_jobs(),
    }
