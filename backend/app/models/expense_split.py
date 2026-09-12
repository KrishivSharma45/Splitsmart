from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    share_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    shares: Mapped[int | None] = mapped_column(nullable=True)

    expense: Mapped["Expense"] = relationship("Expense", back_populates="splits")
    user: Mapped["User"] = relationship("User")
