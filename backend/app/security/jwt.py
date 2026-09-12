from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import PyJWTError

from app.config import get_settings

settings = get_settings()


class TokenError(Exception):
    pass


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except PyJWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise TokenError("Invalid token type")
    return payload
