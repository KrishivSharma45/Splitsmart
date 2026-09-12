import enum
from datetime import date as date_type
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SettlementStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SettlementStatus] = mapped_column(
        SAEnum(SettlementStatus, native_enum=False), default=SettlementStatus.COMPLETED, nullable=False
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="settlements")
    payer: Mapped["User"] = relationship("User", foreign_keys=[payer_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])
