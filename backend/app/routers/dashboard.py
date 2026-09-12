from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense, ExpenseStatus
from app.models.settlement import Settlement
from app.models.trip import Trip, TripStatus
from app.models.trip_member import MemberStatus, TripMember
from app.models.user import User
from app.routers.expenses import serialize_expense
from app.schemas.dashboard import DashboardSummary
from app.schemas.settlement import SettlementOut
from app.schemas.trip import TripListItem, TripOut
from app.security.deps import get_current_user
from app.services.balance_service import compute_trip_balances, total_active_expenses
from app.utils.money import quantize

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummary)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = (
        db.query(TripMember)
        .filter(TripMember.user_id == current_user.id, TripMember.status == MemberStatus.ACTIVE)
        .all()
    )
    trip_ids = [m.trip_id for m in memberships]
    role_by_trip = {m.trip_id: m.role for m in memberships}

    total_spending = Decimal("0")
    if trip_ids:
        paid_rows = db.query(Expense.amount).filter(
            Expense.paid_by == current_user.id,
            Expense.trip_id.in_(trip_ids),
            Expense.status == ExpenseStatus.ACTIVE,
        )
        total_spending = sum((Decimal(r[0]) for r in paid_rows), Decimal("0"))

    amount_you_owe = Decimal("0")
    amount_owed_to_you = Decimal("0")
    trip_items: list[TripListItem] = []

    for trip_id in trip_ids:
        trip = db.get(Trip, trip_id)
        if trip is None:
            continue
        balances = compute_trip_balances(db, trip_id)
        my_net = balances[current_user.id].net if current_user.id in balances else Decimal("0")
        if my_net > 0:
            amount_owed_to_you += my_net
        elif my_net < 0:
            amount_you_owe += -my_net

        member_count = db.query(TripMember).filter(
            TripMember.trip_id == trip_id, TripMember.status == MemberStatus.ACTIVE
        ).count()
        base = TripOut.model_validate(trip).model_dump()
        base["my_role"] = role_by_trip[trip_id]
        trip_items.append(
            TripListItem(
                **base,
                total_expenses=total_active_expenses(db, trip_id),
                member_count=member_count,
                my_net_balance=my_net,
            )
        )

    trip_items.sort(key=lambda t: t.created_at, reverse=True)
    active_trip_count = sum(1 for t in trip_items if t.status == TripStatus.ACTIVE)

    recent_expenses = []
    recent_settlements = []
    if trip_ids:
        expenses = (
            db.query(Expense)
            .filter(Expense.trip_id.in_(trip_ids))
            .order_by(Expense.created_at.desc())
            .limit(10)
            .all()
        )
        recent_expenses = [serialize_expense(e) for e in expenses]

        settlements = (
            db.query(Settlement)
            .filter(Settlement.trip_id.in_(trip_ids))
            .order_by(Settlement.created_at.desc())
            .limit(10)
            .all()
        )
        recent_settlements = [SettlementOut.model_validate(s) for s in settlements]

    return DashboardSummary(
        total_spending=quantize(total_spending),
        trip_count=len(trip_items),
        active_trip_count=active_trip_count,
        amount_you_owe=quantize(amount_you_owe),
        amount_owed_to_you=quantize(amount_owed_to_you),
        recent_expenses=recent_expenses,
        recent_settlements=recent_settlements,
        trips=trip_items,
    )
