import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.audit.verification_service import verify_chain
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.trip_member import MemberStatus, TripMember
from app.models.user import User
from app.schemas.audit import AuditLogOut, AuditVerifyResponse
from app.security.deps import get_current_user, require_trip_member

router = APIRouter(prefix="/api", tags=["audit"])


def serialize_audit_log(db: Session, record: AuditLog) -> AuditLogOut:
    actor = db.get(User, record.actor_id) if record.actor_id else None
    return AuditLogOut(
        id=record.id,
        event_type=record.event_type,
        actor=actor,
        trip_id=record.trip_id,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        event_data=json.loads(record.event_data),
        timestamp=record.timestamp,
        previous_hash=record.previous_hash,
        current_hash=record.current_hash,
    )


@router.get("/trips/{trip_id}/audit", response_model=list[AuditLogOut])
def list_trip_audit_log(
    trip_id: int,
    event_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog).filter(AuditLog.trip_id == trip_id)
    if event_type:
        q = q.filter(AuditLog.event_type == event_type)
    records = q.order_by(AuditLog.id.desc()).offset(offset).limit(limit).all()
    return [serialize_audit_log(db, r) for r in records]


@router.post("/trips/{trip_id}/audit/verify", response_model=AuditVerifyResponse)
def verify_trip_audit(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    """Runs integrity verification over the ENTIRE global ledger (not just
    this trip's events) -- that's the actual cryptographic guarantee, since
    the audit chain is one system-wide sequence. See AuditVerifyResponse.scope.
    """
    result = verify_chain(db)
    record_event(
        db,
        event_type=AuditEvent.AUDIT_VERIFICATION_RUN,
        entity_type="audit_ledger",
        actor_id=current_user.id,
        trip_id=trip_id,
        entity_id=None,
        event_data={
            "status": result.status,
            "records_checked": result.records_checked,
            "broken_links": result.broken_links,
            "affected_record": result.affected_record,
        },
    )
    db.commit()
    return AuditVerifyResponse(
        status=result.status,
        records_checked=result.records_checked,
        broken_links=result.broken_links,
        affected_record=result.affected_record,
        affected_records=result.affected_records,
        verified_at=result.verified_at,
    )


@router.get("/audit", response_model=list[AuditLogOut])
def list_my_audit_log(
    event_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A user's personal view of the global ledger: their own account
    events plus every event belonging to a trip they're an active member
    of. Never exposes another user's private trip data.
    """
    my_trip_ids = [
        m.trip_id
        for m in db.query(TripMember).filter(
            TripMember.user_id == current_user.id, TripMember.status == MemberStatus.ACTIVE
        )
    ]
    combined_ids: set[int] = set()
    if my_trip_ids:
        trip_scoped = db.query(AuditLog.id).filter(AuditLog.trip_id.in_(my_trip_ids)).all()
        combined_ids |= {row[0] for row in trip_scoped}
    own_events = (
        db.query(AuditLog.id).filter(AuditLog.trip_id.is_(None), AuditLog.actor_id == current_user.id).all()
    )
    combined_ids |= {row[0] for row in own_events}

    if event_type:
        combined_query = db.query(AuditLog).filter(AuditLog.id.in_(combined_ids), AuditLog.event_type == event_type)
    else:
        combined_query = db.query(AuditLog).filter(AuditLog.id.in_(combined_ids))

    records = combined_query.order_by(AuditLog.id.desc()).offset(offset).limit(limit).all()
    return [serialize_audit_log(db, r) for r in records]


@router.post("/audit/verify", response_model=AuditVerifyResponse)
def verify_global_audit(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = verify_chain(db)
    record_event(
        db,
        event_type=AuditEvent.AUDIT_VERIFICATION_RUN,
        entity_type="audit_ledger",
        actor_id=current_user.id,
        trip_id=None,
        entity_id=None,
        event_data={
            "status": result.status,
            "records_checked": result.records_checked,
            "broken_links": result.broken_links,
            "affected_record": result.affected_record,
        },
    )
    db.commit()
    return AuditVerifyResponse(
        status=result.status,
        records_checked=result.records_checked,
        broken_links=result.broken_links,
        affected_record=result.affected_record,
        affected_records=result.affected_records,
        verified_at=result.verified_at,
    )
