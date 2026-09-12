from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trip import Trip
from app.models.trip_member import ROLE_RANK, MemberStatus, TripMember, TripRole
from app.models.user import User
from app.schemas.balance import BalancesResponse, DebtEdge, DebtsResponse, MemberBalance
from app.schemas.trip import (
    MemberAddRequest,
    RoleChangeRequest,
    TripCreate,
    TripListItem,
    TripMemberOut,
    TripOut,
    TripUpdate,
)
from app.security.deps import get_current_user, require_trip_member, require_trip_role
from app.services import trip_service
from app.services.balance_service import compute_trip_balances, total_active_expenses
from app.services.debt_simplification import simplify_debts

router = APIRouter(prefix="/api/trips", tags=["trips"])


def _get_trip_or_404(db: Session, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.get("", response_model=list[TripListItem])
def list_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = (
        db.query(TripMember)
        .filter(TripMember.user_id == current_user.id, TripMember.status == MemberStatus.ACTIVE)
        .all()
    )
    items = []
    for m in memberships:
        trip = db.get(Trip, m.trip_id)
        if trip is None:
            continue
        member_count = (
            db.query(TripMember)
            .filter(TripMember.trip_id == trip.id, TripMember.status == MemberStatus.ACTIVE)
            .count()
        )
        balances = compute_trip_balances(db, trip.id)
        my_net = balances[current_user.id].net if current_user.id in balances else 0
        base = TripOut.model_validate(trip).model_dump()
        base["my_role"] = m.role
        items.append(
            TripListItem(
                **base,
                total_expenses=total_active_expenses(db, trip.id),
                member_count=member_count,
                my_net_balance=my_net,
            )
        )
    items.sort(key=lambda t: t.created_at, reverse=True)
    return items


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(data: TripCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trip = trip_service.create_trip(db, current_user, data)
    out = TripOut.model_validate(trip)
    out.my_role = TripRole.OWNER
    return out


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(
    trip_id: int,
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    out = TripOut.model_validate(trip)
    out.my_role = membership.role
    return out


@router.put("/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: int,
    data: TripUpdate,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_role(TripRole.OWNER)),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    trip = trip_service.update_trip(db, trip, current_user, data)
    out = TripOut.model_validate(trip)
    out.my_role = membership.role
    return out


@router.delete("/{trip_id}", response_model=TripOut)
def archive_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_role(TripRole.OWNER)),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    trip = trip_service.archive_trip(db, trip, current_user)
    out = TripOut.model_validate(trip)
    out.my_role = membership.role
    return out


@router.get("/{trip_id}/members", response_model=list[TripMemberOut])
def list_members(
    trip_id: int,
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    members = (
        db.query(TripMember)
        .filter(TripMember.trip_id == trip_id, TripMember.status == MemberStatus.ACTIVE)
        .order_by(TripMember.joined_at.asc())
        .all()
    )
    return members


@router.post("/{trip_id}/members", response_model=TripMemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    trip_id: int,
    data: MemberAddRequest,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_role(TripRole.ADMIN)),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    return trip_service.add_member(db, trip, current_user, data.email, data.role)


@router.delete("/{trip_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    trip_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id and ROLE_RANK[membership.role] < ROLE_RANK[TripRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This action requires ADMIN role or higher")

    trip = _get_trip_or_404(db, trip_id)
    trip_service.remove_member(db, trip, current_user, user_id)
    return None


@router.patch("/{trip_id}/members/{user_id}", response_model=TripMemberOut)
def change_member_role(
    trip_id: int,
    user_id: int,
    data: RoleChangeRequest,
    current_user: User = Depends(get_current_user),
    membership: TripMember = Depends(require_trip_role(TripRole.ADMIN)),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    return trip_service.change_member_role(db, trip, current_user, membership, user_id, data.role)


@router.get("/{trip_id}/balances", response_model=BalancesResponse)
def get_balances(
    trip_id: int,
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    balances = compute_trip_balances(db, trip_id)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(balances.keys()))}
    member_balances = [
        MemberBalance(user=users[uid], total_paid=b.paid, total_owed=b.owed, net_balance=b.net)
        for uid, b in sorted(balances.items(), key=lambda kv: kv[0])
        if uid in users
    ]
    return BalancesResponse(
        trip_id=trip_id,
        currency=trip.currency,
        total_expenses=total_active_expenses(db, trip_id),
        balances=member_balances,
    )


@router.get("/{trip_id}/debts", response_model=DebtsResponse)
def get_debts(
    trip_id: int,
    membership: TripMember = Depends(require_trip_member),
    db: Session = Depends(get_db),
):
    trip = _get_trip_or_404(db, trip_id)
    balances = compute_trip_balances(db, trip_id)
    net_balances = {uid: b.net for uid, b in balances.items()}
    transactions = simplify_debts(net_balances)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(net_balances.keys()))}

    edges = [
        DebtEdge(from_user=users[from_id], to_user=users[to_id], amount=amount)
        for from_id, to_id, amount in transactions
        if from_id in users and to_id in users
    ]
    return DebtsResponse(trip_id=trip_id, currency=trip.currency, simplified_debts=edges, transaction_count=len(edges))
