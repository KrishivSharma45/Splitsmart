from decimal import Decimal

from pydantic import BaseModel

from app.schemas.balance import MemberBalance
from app.schemas.settlement import SettlementOut
from app.schemas.trip import TripOut


class CategoryBreakdownItem(BaseModel):
    category: str
    total: Decimal
    percentage_of_total: Decimal


class ReportSummary(BaseModel):
    trip: TripOut
    total_expenses: Decimal
    active_expense_count: int
    voided_expense_count: int
    balances: list[MemberBalance]
    settlements: list[SettlementOut]
    category_breakdown: list[CategoryBreakdownItem]
