from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

GENESIS_HASH = "0" * 64


class AuditLog(Base):
    """Append-only cryptographic audit ledger.

    No router or service ever issues an UPDATE/DELETE against this table --
    the only write path is audit.audit_service.record_event().
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
