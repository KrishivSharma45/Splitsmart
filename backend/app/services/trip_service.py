from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.audit_service import record_event
from app.audit.events import AuditEvent
from app.models.trip import Trip, TripStatus
from app.models.trip_member import MemberStatus, TripMember, TripRole
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate
from app.services.notification_service import create_notification


def create_trip(db: Session, current_user: User, data: TripCreate) -> Trip:
    trip = Trip(
        name=data.name,
        description=data.description,
        destination=data.destination,
        start_date=data.start_date,
        end_date=data.end_date,
        currency=data.currency,
        created_by=current_user.id,
    )
    db.add(trip)
    db.flush()

    membership = TripMember(trip_id=trip.id, user_id=current_user.id, role=TripRole.OWNER)
    db.add(membership)
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.TRIP_CREATED,
        entity_type="trip",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"name": trip.name, "currency": trip.currency},
    )
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, trip: Trip, current_user: User, data: TripUpdate) -> Trip:
    previous_state = {
        "name": trip.name,
        "description": trip.description,
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
        "currency": trip.currency,
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    db.flush()

    new_state = {
        "name": trip.name,
        "description": trip.description,
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
        "currency": trip.currency,
    }

    record_event(
        db,
        event_type=AuditEvent.TRIP_UPDATED,
        entity_type="trip",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"previous": previous_state, "new": new_state},
    )
    db.commit()
    db.refresh(trip)
    return trip


def archive_trip(db: Session, trip: Trip, current_user: User) -> Trip:
    if trip.status == TripStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trip is already archived")

    trip.status = TripStatus.ARCHIVED
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.TRIP_ARCHIVED,
        entity_type="trip",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=trip.id,
        event_data={"name": trip.name},
    )
    db.commit()
    db.refresh(trip)
    return trip


def add_member(db: Session, trip: Trip, current_user: User, email: str, role: TripRole) -> TripMember:
    target_user = db.query(User).filter(User.email == email).first()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found with that email")

    existing = (
        db.query(TripMember).filter(TripMember.trip_id == trip.id, TripMember.user_id == target_user.id).first()
    )
    if existing is not None:
        if existing.status == MemberStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this trip")
        existing.status = MemberStatus.ACTIVE
        existing.role = role
        membership = existing
    else:
        membership = TripMember(trip_id=trip.id, user_id=target_user.id, role=role)
        db.add(membership)
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.MEMBER_ADDED,
        entity_type="trip_member",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=membership.id,
        event_data={"user_id": target_user.id, "email": target_user.email, "role": role.value},
    )
    create_notification(
        db,
        user_id=target_user.id,
        type="MEMBER_ADDED",
        message=f"You were added to {trip.name}.",
        trip_id=trip.id,
        entity_type="trip",
        entity_id=trip.id,
    )
    db.commit()
    db.refresh(membership)
    return membership


def remove_member(db: Session, trip: Trip, current_user: User, target_user_id: int) -> None:
    membership = (
        db.query(TripMember)
        .filter(
            TripMember.trip_id == trip.id,
            TripMember.user_id == target_user_id,
            TripMember.status == MemberStatus.ACTIVE,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this trip")

    if membership.role == TripRole.OWNER:
        remaining_owners = (
            db.query(TripMember)
            .filter(
                TripMember.trip_id == trip.id,
                TripMember.role == TripRole.OWNER,
                TripMember.status == MemberStatus.ACTIVE,
                TripMember.id != membership.id,
            )
            .count()
        )
        if remaining_owners == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Cannot remove the only owner of the trip"
            )

    membership.status = MemberStatus.REMOVED
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.MEMBER_REMOVED,
        entity_type="trip_member",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=membership.id,
        event_data={"user_id": target_user_id},
    )
    db.commit()


def change_member_role(
    db: Session,
    trip: Trip,
    current_user: User,
    actor_membership: TripMember,
    target_user_id: int,
    new_role: TripRole,
) -> TripMember:
    if actor_membership.role != TripRole.OWNER and (
        new_role == TripRole.OWNER or actor_membership.user_id == target_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the trip owner can grant the OWNER role or change their own role",
        )

    membership = (
        db.query(TripMember)
        .filter(
            TripMember.trip_id == trip.id,
            TripMember.user_id == target_user_id,
            TripMember.status == MemberStatus.ACTIVE,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this trip")

    if actor_membership.role != TripRole.OWNER and membership.role == TripRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the trip owner can change another owner's role"
        )

    if membership.role == TripRole.OWNER and new_role != TripRole.OWNER:
        remaining_owners = (
            db.query(TripMember)
            .filter(
                TripMember.trip_id == trip.id,
                TripMember.role == TripRole.OWNER,
                TripMember.status == MemberStatus.ACTIVE,
                TripMember.id != membership.id,
            )
            .count()
        )
        if remaining_owners == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Cannot demote the only owner of the trip"
            )

    previous_role = membership.role
    membership.role = new_role
    db.flush()

    record_event(
        db,
        event_type=AuditEvent.ROLE_CHANGED,
        entity_type="trip_member",
        actor_id=current_user.id,
        trip_id=trip.id,
        entity_id=membership.id,
        event_data={"user_id": target_user_id, "previous_role": previous_role.value, "new_role": new_role.value},
    )
    create_notification(
        db,
        user_id=target_user_id,
        type="ROLE_CHANGED",
        message=f"Your role in {trip.name} changed to {new_role.value}.",
        trip_id=trip.id,
        entity_type="trip",
        entity_id=trip.id,
    )
    db.commit()
    db.refresh(membership)
    return membership
