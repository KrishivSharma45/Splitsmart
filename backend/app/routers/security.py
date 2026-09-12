from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit.events import AuditEvent
from app.audit.verification_service import verify_chain
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.security_event import SecurityEvent
from app.models.trip_member import MemberStatus, TripMember
from app.models.user import User
from app.routers.audit import serialize_audit_log
from app.schemas.security import SecurityEventOut, SecurityOverview
from app.security.deps import get_current_user

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/overview", response_model=SecurityOverview)
def get_security_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database_status = "CONNECTED"
    except Exception:
        database_status = "DISCONNECTED"

    result = verify_chain(db)

    last_verification_record = (
        db.query(AuditLog)
        .filter(AuditLog.event_type == AuditEvent.AUDIT_VERIFICATION_RUN)
        .order_by(AuditLog.id.desc())
        .first()
    )
    last_verification_at = last_verification_record.timestamp if last_verification_record else None

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    active_users_24h = (
        db.query(AuditLog.actor_id)
        .filter(AuditLog.event_type == AuditEvent.USER_LOGIN, AuditLog.timestamp >= since)
        .distinct()
        .count()
    )
    failed_logins_24h = (
        db.query(SecurityEvent).filter(SecurityEvent.event_type == "LOGIN_FAILED", SecurityEvent.created_at >= since).count()
    )

    my_trip_ids = [
        m.trip_id
        for m in db.query(TripMember).filter(
            TripMember.user_id == current_user.id, TripMember.status == MemberStatus.ACTIVE
        )
    ]
    audit_ids: set[int] = set()
    if my_trip_ids:
        audit_ids |= {r[0] for r in db.query(AuditLog.id).filter(AuditLog.trip_id.in_(my_trip_ids))}
    audit_ids |= {
        r[0]
        for r in db.query(AuditLog.id).filter(AuditLog.trip_id.is_(None), AuditLog.actor_id == current_user.id)
    }
    recent_audit_records = (
        db.query(AuditLog).filter(AuditLog.id.in_(audit_ids)).order_by(AuditLog.id.desc()).limit(20).all()
    )
    recent_audit_events = [serialize_audit_log(db, r) for r in recent_audit_records]

    recent_security_records = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.user_id == current_user.id)
        .order_by(SecurityEvent.id.desc())
        .limit(20)
        .all()
    )
    recent_security_events = [SecurityEventOut.model_validate(r, from_attributes=True) for r in recent_security_records]

    return SecurityOverview(
        database_status=database_status,
        audit_chain_status=result.status,
        total_audit_events=result.records_checked,
        last_verification_at=last_verification_at,
        last_verification_status=result.status,
        integrity_violations=result.broken_links,
        recent_security_events=recent_security_events,
        recent_audit_events=recent_audit_events,
        active_users_24h=active_users_24h,
        failed_logins_24h=failed_logins_24h,
    )
