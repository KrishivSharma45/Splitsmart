from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.expense import ExpenseCategory, ExpenseStatus, SplitMethod
from app.schemas.user import UserSummary


class ExpenseParticipantInput(BaseModel):
    user_id: int
    amount: Decimal | None = None
    percentage: Decimal | None = None
    shares: int | None = None


class ExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    currency: str = "INR"
    paid_by: int
    category: ExpenseCategory = ExpenseCategory.OTHER
    split_method: SplitMethod
    date: date_type
    notes: str | None = None
    participants: list[ExpenseParticipantInput] = Field(min_length=1)

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Expense amount must be greater than zero")
        return v

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be blank")
        return v.strip()


class ExpenseUpdate(BaseModel):
    description: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    paid_by: int | None = None
    category: ExpenseCategory | None = None
    split_method: SplitMethod | None = None
    date: date_type | None = None
    notes: str | None = None
    participants: list[ExpenseParticipantInput] | None = None


class VoidExpenseRequest(BaseModel):
    reason: str | None = None


class ExpenseSplitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserSummary
    share_amount: Decimal
    percentage: Decimal | None
    shares: int | None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    description: str
    amount: Decimal
    currency: str
    paid_by: UserSummary
    category: ExpenseCategory
    split_method: SplitMethod
    date: date_type
    notes: str | None
    status: ExpenseStatus
    void_reason: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    splits: list[ExpenseSplitOut] = []
    has_receipt: bool = False
