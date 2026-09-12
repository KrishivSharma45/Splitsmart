from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.expense import Expense, ExpenseStatus
from app.models.expense_split import ExpenseSplit
from app.models.settlement import Settlement, SettlementStatus
from app.models.trip_member import MemberStatus, TripMember
from app.utils.money import quantize


@dataclass
class UserBalance:
    paid: Decimal
    owed: Decimal
    net: Decimal


def compute_trip_balances(db: Session, trip_id: int) -> dict[int, UserBalance]:
    """The backend's single source of truth for who paid what, owes what,
    and their net position, for a given trip.

    net_balance[user] = total_paid - total_owed + settlements_paid - settlements_received
    Positive net => the user should receive money. Negative => the user owes money.
    """
    member_ids = {
        m.user_id
        for m in db.query(TripMember).filter(
            TripMember.trip_id == trip_id, TripMember.status == MemberStatus.ACTIVE
        )
    }

    paid: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    owed: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    settlement_adjustment: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    paid_rows = db.query(Expense.paid_by, Expense.amount).filter(
        Expense.trip_id == trip_id, Expense.status == ExpenseStatus.ACTIVE
    )
    for paid_by, amount in paid_rows:
        paid[paid_by] += Decimal(amount)

    split_rows = (
        db.query(ExpenseSplit.user_id, ExpenseSplit.share_amount)
        .join(Expense, Expense.id == ExpenseSplit.expense_id)
        .filter(Expense.trip_id == trip_id, Expense.status == ExpenseStatus.ACTIVE)
    )
    for user_id, share_amount in split_rows:
        owed[user_id] += Decimal(share_amount)

    settlement_rows = db.query(Settlement.payer_id, Settlement.receiver_id, Settlement.amount).filter(
        Settlement.trip_id == trip_id, Settlement.status == SettlementStatus.COMPLETED
    )
    for payer_id, receiver_id, amount in settlement_rows:
        settlement_adjustment[payer_id] += Decimal(amount)
        settlement_adjustment[receiver_id] -= Decimal(amount)

    all_user_ids = member_ids | set(paid) | set(owed) | set(settlement_adjustment)

    balances: dict[int, UserBalance] = {}
    for user_id in all_user_ids:
        p = quantize(paid[user_id])
        o = quantize(owed[user_id])
        s = quantize(settlement_adjustment[user_id])
        net = quantize(p - o + s)
        balances[user_id] = UserBalance(paid=p, owed=o, net=net)

    return balances


def total_active_expenses(db: Session, trip_id: int) -> Decimal:
    total = db.query(Expense.amount).filter(
        Expense.trip_id == trip_id, Expense.status == ExpenseStatus.ACTIVE
    )
    return quantize(sum((Decimal(row[0]) for row in total), Decimal("0")))
