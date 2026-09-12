from decimal import Decimal

from pydantic import BaseModel

from app.schemas.expense import ExpenseOut
from app.schemas.settlement import SettlementOut
from app.schemas.trip import TripListItem


class DashboardSummary(BaseModel):
    total_spending: Decimal
    trip_count: int
    active_trip_count: int
    amount_you_owe: Decimal
    amount_owed_to_you: Decimal
    recent_expenses: list[ExpenseOut]
    recent_settlements: list[SettlementOut]
    trips: list[TripListItem]
