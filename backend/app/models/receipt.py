from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    expense: Mapped["Expense"] = relationship("Expense", back_populates="receipts")
