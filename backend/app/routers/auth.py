from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.config import get_settings
from app.database import get_db
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut, UserUpdate
from app.security.deps import get_client_ip, get_current_user
from app.security.jwt import create_access_token
from app.security.password import hash_password, verify_password
from app.security.rate_limit import limiter
from app.security.tokens import (
    REFRESH_COOKIE_NAME,
    get_valid_refresh_token,
    issue_refresh_token,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/api/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, response: Response, data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = User(email=data.email, full_name=data.full_name, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.USER_REGISTERED,
        entity_type="user",
        actor_id=user.id,
        entity_id=user.id,
        event_data={"email": user.email, "full_name": user.full_name},
    )
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    raw_refresh, _ = issue_refresh_token(db, user.id)
    db.commit()
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, response: Response, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    client_ip = get_client_ip(request)

    if user is None or not verify_password(data.password, user.hashed_password):
        db.add(SecurityEvent(event_type="LOGIN_FAILED", user_id=user.id if user else None, ip_address=client_ip, detail=f"Failed login attempt for {data.email}"))
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This account has been deactivated")

    record_event(
        db,
        event_type=AuditEvent.USER_LOGIN,
        entity_type="user",
        actor_id=user.id,
        entity_id=user.id,
        event_data={"ip_address": client_ip},
    )
    db.commit()

    access_token = create_access_token(user.id)
    raw_refresh, _ = issue_refresh_token(db, user.id)
    db.commit()
    _set_refresh_cookie(response, raw_refresh)

    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    record = get_valid_refresh_token(db, raw_token)
    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or expired")

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    revoke_refresh_token(db, raw_token)
    new_raw_refresh, _ = issue_refresh_token(db, user.id)
    db.commit()
    _set_refresh_cookie(response, new_raw_refresh)

    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        revoke_refresh_token(db, raw_token)

    record_event(
        db,
        event_type=AuditEvent.USER_LOGOUT,
        entity_type="user",
        actor_id=current_user.id,
        entity_id=current_user.id,
        event_data={},
    )
    db.commit()
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")
    return None


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.full_name is not None:
        stripped = data.full_name.strip()
        if not stripped:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name cannot be blank")
        current_user.full_name = stripped
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(data.new_password)
    revoke_all_refresh_tokens_for_user(db, current_user.id)

    record_event(
        db,
        event_type=AuditEvent.PASSWORD_CHANGED,
        entity_type="user",
        actor_id=current_user.id,
        entity_id=current_user.id,
        event_data={},
    )
    db.commit()
    return None
