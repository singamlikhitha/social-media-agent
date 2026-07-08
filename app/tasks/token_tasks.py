from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.database import SessionLocal
from app.oauth.models import ConnectedAccount, OAuthState
from app.oauth.token_manager import decrypt_token, encrypt_token
from app.config import settings
from app.utils.logger import logger
from app import telemetry
import httpx


@celery_app.task
def refresh_expiring_tokens():
    """Refresh tokens that expire within the next hour."""
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() + timedelta(hours=1)
        accounts = (
            db.query(ConnectedAccount)
            .filter(
                ConnectedAccount.is_active == 1,
                ConnectedAccount.token_expires_at.isnot(None),
                ConnectedAccount.token_expires_at <= threshold,
                ConnectedAccount.refresh_token_enc.isnot(None),
            )
            .all()
        )

        refreshed = 0
        for account in accounts:
            try:
                if account.platform == "youtube":
                    _refresh_google_token(account, db)
                    refreshed += 1
                elif account.platform == "twitter":
                    _refresh_twitter_token(account, db)
                    refreshed += 1
                elif account.platform in ("instagram", "facebook"):
                    _refresh_meta_token(account, db)
                    refreshed += 1
                # LinkedIn doesn't support refresh tokens in this flow
                else:
                    continue
                telemetry.token_refreshes.add(1, {"platform": account.platform, "status": "success"})
            except Exception as e:
                telemetry.token_refreshes.add(1, {"platform": account.platform, "status": "error"})
                logger.error(f"Failed to refresh token for account {account.id}: {e}")

        logger.info(f"Refreshed {refreshed} tokens")
        return {"refreshed": refreshed}
    finally:
        db.close()


def _refresh_google_token(account: ConnectedAccount, db):
    refresh_token = decrypt_token(account.refresh_token_enc)

    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    data = response.json()

    if "access_token" in data:
        account.access_token_enc = encrypt_token(data["access_token"])
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
        db.commit()
        logger.info(f"Refreshed Google token for account {account.id}")
    else:
        logger.error(f"Google token refresh failed for account {account.id}: {data}")


def _refresh_twitter_token(account: ConnectedAccount, db):
    refresh_token = decrypt_token(account.refresh_token_enc)

    response = httpx.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "client_id": settings.TWITTER_CLIENT_ID,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        auth=(settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    data = response.json()

    if "access_token" in data:
        account.access_token_enc = encrypt_token(data["access_token"])
        if data.get("refresh_token"):
            account.refresh_token_enc = encrypt_token(data["refresh_token"])
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 7200))
        db.commit()
        logger.info(f"Refreshed Twitter token for account {account.id}")
    else:
        logger.error(f"Twitter token refresh failed for account {account.id}: {data}")


def _refresh_meta_token(account: ConnectedAccount, db):
    access_token = decrypt_token(account.access_token_enc)

    response = httpx.get(
        "https://graph.facebook.com/v21.0/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": access_token,
        },
        timeout=30,
    )
    data = response.json()

    if "access_token" in data:
        account.access_token_enc = encrypt_token(data["access_token"])
        expires_in = data.get("expires_in", 5184000)
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        db.commit()
        logger.info(f"Refreshed Meta token for account {account.id}")
    else:
        logger.error(f"Meta token refresh failed for account {account.id}: {data}")


@celery_app.task
def cleanup_expired_states():
    """Remove OAuth states older than 10 minutes."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        deleted = db.query(OAuthState).filter(OAuthState.created_at < cutoff).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted} expired OAuth states")
        return {"deleted": deleted}
    finally:
        db.close()
