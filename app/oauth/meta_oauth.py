import secrets
from datetime import datetime, timedelta
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

router = APIRouter(prefix="/api/oauth/meta", tags=["oauth-meta"])

META_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
META_GRAPH_URL = "https://graph.facebook.com/v21.0"

SCOPES = "instagram_basic,instagram_content_publish,instagram_manage_insights,pages_show_list,pages_read_engagement,pages_manage_posts"


@router.get("/authorize")
async def authorize(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.meta_configured:
        raise HTTPException(status_code=400, detail="Meta OAuth not configured")

    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        state=state,
        user_id=current_user.id,
        platform="meta",
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
    }
    auth_url = f"{META_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    # Verify state
    oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # Check TTL (10 minutes)
    from datetime import timezone
    age = datetime.now(timezone.utc) - oauth_state.created_at.replace(tzinfo=timezone.utc)
    if age.total_seconds() > 600:
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(status_code=400, detail="OAuth state expired")

    user_id = oauth_state.user_id
    db.delete(oauth_state)
    db.commit()

    # Exchange code for short-lived token
    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.get(META_TOKEN_URL, params={
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": settings.META_REDIRECT_URI,
            "code": code,
        })
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_data['error']}")

    short_token = token_data["access_token"]

    # Exchange for long-lived token (60 days)
    async with httpx.AsyncClient(timeout=30) as client:
        ll_resp = await client.get(META_TOKEN_URL, params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_token,
        })
        ll_data = ll_resp.json()

    long_token = ll_data.get("access_token", short_token)
    expires_in = ll_data.get("expires_in", 5184000)  # Default 60 days
    token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get user's Instagram Business Account
    async with httpx.AsyncClient(timeout=30) as client:
        # Get pages
        pages_resp = await client.get(f"{META_GRAPH_URL}/me/accounts", params={
            "access_token": long_token,
        })
        pages_data = pages_resp.json()

    connected = []

    # Connect Facebook Pages
    for page in pages_data.get("data", []):
        page_token = page.get("access_token", long_token)
        store_tokens(
            db=db,
            user_id=user_id,
            platform="facebook",
            platform_user_id=page["id"],
            access_token=page_token,
            token_expires_at=token_expires,
            platform_username=page.get("name"),
            scopes=SCOPES,
            profile_data={"page_name": page.get("name"), "category": page.get("category")},
        )
        connected.append({"platform": "facebook", "name": page.get("name")})

        # Check for Instagram Business Account linked to this page
        async with httpx.AsyncClient(timeout=15) as client:
            ig_resp = await client.get(
                f"{META_GRAPH_URL}/{page['id']}",
                params={
                    "fields": "instagram_business_account",
                    "access_token": page_token,
                },
            )
            ig_data = ig_resp.json()

        ig_account = ig_data.get("instagram_business_account")
        if ig_account:
            ig_id = ig_account["id"]
            # Fetch Instagram profile
            async with httpx.AsyncClient(timeout=15) as client:
                profile_resp = await client.get(
                    f"{META_GRAPH_URL}/{ig_id}",
                    params={
                        "fields": "username,followers_count,media_count,biography",
                        "access_token": long_token,
                    },
                )
                profile_data = profile_resp.json()

            store_tokens(
                db=db,
                user_id=user_id,
                platform="instagram",
                platform_user_id=ig_id,
                access_token=long_token,
                token_expires_at=token_expires,
                platform_username=profile_data.get("username"),
                scopes=SCOPES,
                profile_data=profile_data,
            )
            connected.append({"platform": "instagram", "username": profile_data.get("username")})

    # Redirect to frontend with success
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/accounts?connected={'|'.join(c['platform'] for c in connected)}"
    )
