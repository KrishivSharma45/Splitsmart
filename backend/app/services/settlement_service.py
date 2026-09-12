from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.models.settlement import Settlement, SettlementStatus
from app.models.trip import Trip
from app.models.trip_member import MemberStatus, TripMember
from app.models.user import User
from app.schemas.settlement import SettlementCreate
from app.services.notification_service import create_notification
from app.utils.money import quantize


def create_settlement(db: Session, trip: Trip, current_user: User, data: SettlementCreate) -> Settlement:
    active_ids = {
        m.user_id
        for m in db.query(TripMember).filter(TripMember.trip_id == trip.id, TripMember.status == MemberStatus.ACTIVE)
    }
    if data.payer_id not in active_ids or data.receiver_id not in active_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both payer and receiver must be active members of this trip",
        )

    settlement = Settlement(
        trip_id=trip.id,
        payer_id=data.payer_id,
        receiver_id=data.receiver_id,
        amount=quantize(data.amount),
        currency=data.currency,
        date=data.date,
        note=data.note,
        created_by=current_user.id,
        status=SettlementStatus.COMPLETED,
    )
    db.add(settlement)
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.SETTLEMENT_CREATED,
        entity_type="settlement",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=settlement.id,
        event_data={
            "payer_id": settlement.payer_id,
            "receiver_id": settlement.receiver_id,
            "amount": str(settlement.amount),
            "currency": settlement.currency,
        },
    )

    for uid in {data.payer_id, data.receiver_id} - {current_user.id}:
        create_notification(
            db,
            user_id=uid,
            type="SETTLEMENT_CREATED",
            message=f"A settlement of {settlement.currency} {settlement.amount} was recorded in {trip.name}.",
            trip_id=trip.id,
            entity_type="settlement",
            entity_id=settlement.id,
        )

    db.commit()
    db.refresh(settlement)
    return settlement


def cancel_settlement(db: Session, settlement: Settlement, current_user: User) -> Settlement:
    if settlement.status == SettlementStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Settlement is already cancelled")

    settlement.status = SettlementStatus.CANCELLED
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.SETTLEMENT_CANCELLED,
        entity_type="settlement",
        actor_id=current_user.id,
        trip_id=settlement.trip_id,
        entity_id=settlement.id,
        event_data={
            "payer_id": settlement.payer_id,
            "receiver_id": settlement.receiver_id,
            "amount": str(settlement.amount),
        },
    )
    db.commit()
    db.refresh(settlement)
    return settlement
