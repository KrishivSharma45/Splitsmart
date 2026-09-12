import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TripRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


ROLE_RANK = {TripRole.MEMBER: 0, TripRole.ADMIN: 1, TripRole.OWNER: 2}


class TripMember(Base):
    __tablename__ = "trip_members"
    __table_args__ = (UniqueConstraint("trip_id", "user_id", name="uq_trip_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[TripRole] = mapped_column(SAEnum(TripRole, native_enum=False), default=TripRole.MEMBER, nullable=False)
    status: Mapped[MemberStatus] = mapped_column(
        SAEnum(MemberStatus, native_enum=False), default=MemberStatus.ACTIVE, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="trip_memberships", foreign_keys=[user_id])
