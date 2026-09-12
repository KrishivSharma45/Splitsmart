from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settlement import Settlement
from app.models.trip import Trip
from app.models.trip_member import ROLE_RANK, TripMember, TripRole
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementOut
from app.security.deps import get_current_user, get_trip_membership, require_trip_member
from app.services import settlement_service

router = APIRouter(prefix="/api", tags=["settlements"])


@router.get("/trips/{trip_id}/settlements", response_model=list[SettlementOut])
def list_settlements(
    trip_id: int,
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    settlements = (
        db.query(Settlement)
        .filter(Settlement.trip_id == trip_id)
        .order_by(Settlement.date.desc(), Settlement.id.desc())
        .all()
    )
    return settlements


@router.post("/trips/{trip_id}/settlements", response_model=SettlementOut, status_code=status.HTTP_201_CREATED)
def create_settlement(
    trip_id: int,
    data: SettlementCreate,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return settlement_service.create_settlement(db, trip, current_user, data)


@router.post("/settlements/{settlement_id}/cancel", response_model=SettlementOut)
def cancel_settlement(
    settlement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settlement = db.get(Settlement, settlement_id)
    if settlement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

    membership = get_trip_membership(settlement.trip_id, db, current_user)
    if settlement.created_by != current_user.id and ROLE_RANK[membership.role] < ROLE_RANK[TripRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the settlement creator or a trip admin/owner can cancel this settlement",
        )

    return settlement_service.cancel_settlement(db, settlement, current_user)
