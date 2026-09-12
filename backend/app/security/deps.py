from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trip_member import ROLE_RANK, MemberStatus, TripMember, TripRole
from app.models.user import User
from app.security.jwt import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_trip_membership(trip_id: int, db: Session, user: User) -> TripMember:
    membership = (
        db.query(TripMember)
        .filter(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user.id,
            TripMember.status == MemberStatus.ACTIVE,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this trip")
    return membership


def require_trip_member(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripMember:
    return get_trip_membership(trip_id, db, current_user)


def require_trip_role(minimum_role: TripRole):
    def _dependency(
        trip_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> TripMember:
        membership = get_trip_membership(trip_id, db, current_user)
        if ROLE_RANK[membership.role] < ROLE_RANK[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires {minimum_role.value} role or higher",
            )
        return membership

    return _dependency
