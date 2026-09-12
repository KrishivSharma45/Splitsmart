import enum
from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TripStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        SAEnum(TripStatus, native_enum=False), default=TripStatus.ACTIVE, nullable=False
    )
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

    members: Mapped[list["TripMember"]] = relationship(
        "TripMember", back_populates="trip", cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="trip")
    settlements: Mapped[list["Settlement"]] = relationship("Settlement", back_populates="trip")
