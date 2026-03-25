from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.auth.service import decode_token
from app.config import settings
from app.utils.logger import logger
import uuid


class PlanEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforce plan limits on post creation."""

    async def dispatch(self, request: Request, call_next):
        # Only check POST to /api/posts
        if request.method == "POST" and request.url.path == "/api/posts":
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub")
                    if user_id:
                        await self._check_post_limit(uuid.UUID(user_id))

        return await call_next(request)

    async def _check_post_limit(self, user_id: uuid.UUID):
        from app.auth.models import User
        from app.models.post import ScheduledPost

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return

            # Get monthly post count
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            post_count = (
                db.query(ScheduledPost)
                .filter(
                    ScheduledPost.user_id == user_id,
                    ScheduledPost.created_at >= month_start,
                )
                .count()
            )

            max_posts = {
                "free": settings.FREE_PLAN_MAX_POSTS_PER_MONTH,
                "pro": settings.PRO_PLAN_MAX_POSTS_PER_MONTH,
                "enterprise": 999999,
            }

            limit = max_posts.get(user.plan_tier, settings.FREE_PLAN_MAX_POSTS_PER_MONTH)

            if post_count >= limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Monthly post limit reached ({limit} posts). Upgrade your plan for more.",
                )
        finally:
            db.close()
