import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.refresh_token import RefreshToken

settings = get_settings()

REFRESH_COOKIE_NAME = "splitsmart_refresh_token"


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_refresh_token(db: Session, user_id: int) -> tuple[str, datetime]:
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    record = RefreshToken(user_id=user_id, token_hash=_hash_token(raw_token), expires_at=expires_at)
    db.add(record)
    db.flush()
    return raw_token, expires_at


def get_valid_refresh_token(db: Session, raw_token: str) -> RefreshToken | None:
    token_hash = _hash_token(raw_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if record is None:
        return None
    if record.revoked:
        return None
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    return record


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = _hash_token(raw_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if record is not None:
        record.revoked = True
        db.flush()


def revoke_all_refresh_tokens_for_user(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)).update(
        {"revoked": True}
    )
    db.flush()
