from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.settlement import SettlementStatus
from app.schemas.user import UserSummary


class SettlementCreate(BaseModel):
    payer_id: int
    receiver_id: int
    amount: Decimal
    currency: str = "INR"
    date: date
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Settlement amount must be greater than zero")
        return v

    @field_validator("receiver_id")
    @classmethod
    def payer_receiver_differ(cls, v: int, info) -> int:
        payer_id = info.data.get("payer_id")
        if payer_id is not None and payer_id == v:
            raise ValueError("Payer and receiver must be different members")
        return v


class SettlementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    payer: UserSummary
    receiver: UserSummary
    amount: Decimal
    currency: str
    date: date
    note: str | None
    status: SettlementStatus
    created_by: int
    created_at: datetime
