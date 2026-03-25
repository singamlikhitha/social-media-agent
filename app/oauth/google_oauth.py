import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
from app.database import get_db
from app.config import settings
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.oauth.models import OAuthState
from app.oauth.token_manager import store_tokens
from app.utils.logger import logger

router = APIRouter(prefix="/api/oauth/google", tags=["oauth-google"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl"


@router.get("/authorize")
async def authorize(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.google_configured:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        platform="google",
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    # If redirect=true, redirect directly; otherwise return JSON
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    age = datetime.now(timezone.utc) - oauth_state.created_at.replace(tzinfo=timezone.utc)
    if age.total_seconds() > 600:
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=400, detail="OAuth state expired")

    user_id = oauth_state.user_id
    db.delete(oauth_state)
    db.commit()

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "code": code,
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_data['error']}")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get YouTube channel info
    async with httpx.AsyncClient(timeout=15) as client:
        channel_resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet,statistics", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        channel_data = channel_resp.json()

    channel = channel_data.get("items", [{}])[0] if channel_data.get("items") else {}
    channel_id = channel.get("id", "unknown")
    snippet = channel.get("snippet", {})

    store_tokens(
        db=db,
        user_id=user_id,
        platform="youtube",
        platform_user_id=channel_id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires,
        platform_username=snippet.get("title"),
        scopes=SCOPES,
        profile_data={
            "channel_title": snippet.get("title"),
            "description": snippet.get("description", "")[:200],
            "subscriber_count": channel.get("statistics", {}).get("subscriberCount"),
            "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url"),
        },
    )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/accounts?connected=youtube"
    )
