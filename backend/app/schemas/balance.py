from decimal import Decimal

from pydantic import BaseModel

from app.schemas.user import UserSummary


class MemberBalance(BaseModel):
    user: UserSummary
    total_paid: Decimal
    total_owed: Decimal
    net_balance: Decimal


class BalancesResponse(BaseModel):
    trip_id: int
    currency: str
    total_expenses: Decimal
    balances: list[MemberBalance]


class DebtEdge(BaseModel):
    from_user: UserSummary
    to_user: UserSummary
    amount: Decimal


class DebtsResponse(BaseModel):
    trip_id: int
    currency: str
    simplified_debts: list[DebtEdge]
    transaction_count: int
