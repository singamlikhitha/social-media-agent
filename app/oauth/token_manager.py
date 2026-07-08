import os
import base64
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session
from app.config import settings
from app.oauth.models import ConnectedAccount
from app.utils.logger import logger


def _get_encryption_key() -> bytes:
    key_b64 = settings.TOKEN_ENCRYPTION_KEY
    if not key_b64:
        # Generate a random key for development (not for production!)
        logger.warning("TOKEN_ENCRYPTION_KEY not set, using random key (tokens won't survive restarts)")
        return AESGCM.generate_key(bit_length=256)
    return base64.b64decode(key_b64)


_cached_key: bytes | None = None


def _get_key() -> bytes:
    global _cached_key
    if _cached_key is None:
        _cached_key = _get_encryption_key()
    return _cached_key


def encrypt_token(plaintext: str) -> bytes:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext  # Prepend nonce for decryption


def decrypt_token(data: bytes) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = data[:12]
    ciphertext = data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def store_tokens(
    db: Session,
    user_id: uuid.UUID,
    platform: str,
    platform_user_id: str,
    access_token: str,
    refresh_token: str | None = None,
    token_expires_at=None,
    platform_username: str | None = None,
    scopes: str | None = None,
    profile_data: dict | None = None,
) -> ConnectedAccount:
    access_enc = encrypt_token(access_token)
    refresh_enc = encrypt_token(refresh_token) if refresh_token else None

    # Upsert: check if account exists
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.platform == platform,
            ConnectedAccount.platform_user_id == platform_user_id,
        )
        .first()
    )

    if account:
        account.access_token_enc = access_enc
        account.refresh_token_enc = refresh_enc
        account.token_expires_at = token_expires_at
        account.platform_username = platform_username or account.platform_username
        account.scopes = scopes or account.scopes
        account.profile_data = profile_data or account.profile_data
        account.is_active = 1
    else:
        account = ConnectedAccount(
            user_id=user_id,
            platform=platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            token_expires_at=token_expires_at,
            scopes=scopes,
            profile_data=profile_data,
        )
        db.add(account)

    db.commit()
    db.refresh(account)
    logger.info(f"Stored tokens for user {user_id}, platform {platform}")
    return account


def get_platform_credentials(user_id: uuid.UUID, platform: str, db: Session) -> dict | None:
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.platform == platform,
            ConnectedAccount.is_active == 1,
        )
        .first()
    )
    if not account:
        return None

    result = {
        "account_id": account.id,
        "platform_user_id": account.platform_user_id,
        "platform_username": account.platform_username,
        "access_token": decrypt_token(account.access_token_enc),
        "token_expires_at": account.token_expires_at,
        "profile_data": account.profile_data,
    }

    if account.refresh_token_enc:
        result["refresh_token"] = decrypt_token(account.refresh_token_enc)

    return result


def get_all_user_accounts(user_id: uuid.UUID, db: Session) -> list[dict]:
    accounts = (
        db.query(ConnectedAccount)
        .filter(ConnectedAccount.user_id == user_id, ConnectedAccount.is_active == 1)
        .all()
    )
    return [
        {
            "id": a.id,
            "platform": a.platform,
            "platform_user_id": a.platform_user_id,
            "platform_username": a.platform_username,
            "token_expires_at": str(a.token_expires_at) if a.token_expires_at else None,
            "profile_data": a.profile_data,
            "connected_at": str(a.connected_at) if a.connected_at else None,
        }
        for a in accounts
    ]


def disconnect_account(user_id: uuid.UUID, account_id: int, db: Session) -> bool:
    account = (
        db.query(ConnectedAccount)
        .filter(
            ConnectedAccount.id == account_id,
            ConnectedAccount.user_id == user_id,
        )
        .first()
    )
    if not account:
        return False

    account.is_active = 0
    account.access_token_enc = None
    account.refresh_token_enc = None
    db.commit()
    return True
