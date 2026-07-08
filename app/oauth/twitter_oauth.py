import secrets
import hashlib
import base64
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

router = APIRouter(prefix="/api/oauth/twitter", tags=["oauth-twitter"])

TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

SCOPES = "tweet.read tweet.write users.read offline.access"


@router.get("/authorize")
async def authorize(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.twitter_configured:
        raise HTTPException(status_code=400, detail="Twitter OAuth not configured")

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        platform="twitter",
        code_verifier=code_verifier,
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": settings.TWITTER_CLIENT_ID,
        "redirect_uri": settings.TWITTER_REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{TWITTER_AUTH_URL}?{urlencode(params)}"
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
    code_verifier = oauth_state.code_verifier
    db.delete(oauth_state)
    db.commit()

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(
            TWITTER_TOKEN_URL,
            data={
                "client_id": settings.TWITTER_CLIENT_ID,
                "redirect_uri": settings.TWITTER_REDIRECT_URI,
                "code": code,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET),
        )
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_data['error']}")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 7200)
    token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get user info
    async with httpx.AsyncClient(timeout=15) as client:
        user_resp = await client.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "profile_image_url,public_metrics,description"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json().get("data", {})

    store_tokens(
        db=db,
        user_id=user_id,
        platform="twitter",
        platform_user_id=user_data.get("id", "unknown"),
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires,
        platform_username=user_data.get("username"),
        scopes=SCOPES,
        profile_data={
            "name": user_data.get("name"),
            "username": user_data.get("username"),
            "followers_count": user_data.get("public_metrics", {}).get("followers_count"),
            "profile_image_url": user_data.get("profile_image_url"),
        },
    )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/accounts?connected=twitter"
    )
