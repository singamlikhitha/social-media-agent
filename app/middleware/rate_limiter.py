import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.utils.logger import logger

# In-memory rate limiting (use Redis in production)
_request_counts: dict[str, list[float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        # Get client identifier (IP or user from token)
        client_id = request.client.host if request.client else "unknown"

        # Check rate limit
        now = time.time()
        window_start = now - 60

        if client_id not in _request_counts:
            _request_counts[client_id] = []

        # Clean old entries
        _request_counts[client_id] = [t for t in _request_counts[client_id] if t > window_start]

        if len(_request_counts[client_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

        _request_counts[client_id].append(now)

        return await call_next(request)
