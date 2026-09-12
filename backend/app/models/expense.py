import enum
from datetime import date as date_type
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseCategory(str, enum.Enum):
    FOOD = "FOOD"
    TRANSPORT = "TRANSPORT"
    ACCOMMODATION = "ACCOMMODATION"
    SHOPPING = "SHOPPING"
    ENTERTAINMENT = "ENTERTAINMENT"
    BILLS = "BILLS"
    OTHER = "OTHER"


class SplitMethod(str, enum.Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"
    SHARES = "SHARES"


class ExpenseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    VOIDED = "VOIDED"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    paid_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(
        SAEnum(ExpenseCategory, native_enum=False), default=ExpenseCategory.OTHER, nullable=False
    )
    split_method: Mapped[SplitMethod] = mapped_column(SAEnum(SplitMethod, native_enum=False), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        SAEnum(ExpenseStatus, native_enum=False), default=ExpenseStatus.ACTIVE, nullable=False
    )
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="expenses")
    payer: Mapped["User"] = relationship("User", foreign_keys=[paid_by])
    splits: Mapped[list["ExpenseSplit"]] = relationship(
        "ExpenseSplit", back_populates="expense", cascade="all, delete-orphan"
    )
    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", back_populates="expense", cascade="all, delete-orphan"
    )
