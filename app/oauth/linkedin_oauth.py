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

router = APIRouter(prefix="/api/oauth/linkedin", tags=["oauth-linkedin"])

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

SCOPES = "openid profile w_member_social"


@router.get("/authorize")
async def authorize(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.linkedin_configured:
        raise HTTPException(status_code=400, detail="LinkedIn OAuth not configured")

    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        platform="linkedin",
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
    }
    auth_url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
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

    # Exchange code for token
    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_data['error']}")

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)  # 60 days
    token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get user profile
    async with httpx.AsyncClient(timeout=15) as client:
        profile_resp = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_data = profile_resp.json()

    linkedin_id = profile_data.get("sub", "unknown")

    store_tokens(
        db=db,
        user_id=user_id,
        platform="linkedin",
        platform_user_id=linkedin_id,
        access_token=access_token,
        refresh_token=None,  # LinkedIn doesn't provide refresh tokens for this flow
        token_expires_at=token_expires,
        platform_username=profile_data.get("name"),
        scopes=SCOPES,
        profile_data={
            "name": profile_data.get("name"),
            "email": profile_data.get("email"),
            "picture": profile_data.get("picture"),
        },
    )

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/accounts?connected=linkedin"
    )
