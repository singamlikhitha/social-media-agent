from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Social Media SaaS Platform...")
    # Create tables
    try:
        from app.database import Base, engine
        from app.auth.models import User
        from app.oauth.models import ConnectedAccount, OAuthState
        from app.models.post import ScheduledPost
        from app.models.content import ContentIdea
        from app.models.analytics import EngagementMetric
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Migrate trend_source column from VARCHAR(255) to TEXT
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE content_ideas ALTER COLUMN trend_source TYPE TEXT"))
                conn.commit()
                logger.info("Migrated trend_source column to TEXT")
        except Exception as migrate_err:
            logger.info(f"Migration skipped (likely already applied): {migrate_err}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.start()
    except Exception as e:
        logger.error(f"Scheduler start error: {e}")

    yield

    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.shutdown()
    except Exception:
        pass
    logger.info("Application shut down.")


app = FastAPI(
    title="Social Media SaaS Platform",
    description="AI-powered multi-tenant social media management platform",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.plan_enforcement import PlanEnforcementMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(PlanEnforcementMiddleware)

from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.auth.router import router as auth_router
from app.routers import health, posts, content, analytics, media

app.include_router(auth_router)
app.include_router(health.router)
app.include_router(posts.router)
app.include_router(content.router)
app.include_router(analytics.router)
app.include_router(media.router)

# Serve uploaded media files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/api/media/files", StaticFiles(directory=str(uploads_dir)), name="media-files")

# OAuth routers
from app.oauth.meta_oauth import router as meta_oauth_router
from app.oauth.google_oauth import router as google_oauth_router
from app.oauth.twitter_oauth import router as twitter_oauth_router
from app.oauth.linkedin_oauth import router as linkedin_oauth_router
from app.oauth.router import router as oauth_accounts_router
from app.oauth.router import oauth_accounts_flat_router

app.include_router(meta_oauth_router)
app.include_router(google_oauth_router)
app.include_router(twitter_oauth_router)
app.include_router(linkedin_oauth_router)
app.include_router(oauth_accounts_router)
app.include_router(oauth_accounts_flat_router)

# Initialise OpenTelemetry (traces + metrics + logs). No-op unless OTEL_ENABLED=true.
from app.telemetry import setup_telemetry

setup_telemetry(app=app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
