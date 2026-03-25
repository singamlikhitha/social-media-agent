import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary, func, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", "platform_user_id", name="uq_user_platform_account"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # instagram, youtube, facebook, twitter, linkedin
    platform_user_id = Column(String(255))  # Platform-specific user/account ID
    platform_username = Column(String(255))
    access_token_enc = Column(LargeBinary)  # AES-256-GCM encrypted
    refresh_token_enc = Column(LargeBinary)  # AES-256-GCM encrypted
    token_expires_at = Column(DateTime)
    scopes = Column(Text)  # Comma-separated scopes
    profile_data = Column(JSONB)  # Additional profile info
    is_active = Column(Integer, default=1)
    connected_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(20), nullable=False)
    code_verifier = Column(String(255))  # For PKCE flows
    created_at = Column(DateTime, server_default=func.now())
    # States expire after 10 minutes
