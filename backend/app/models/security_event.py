from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecurityEvent(Base):
    """Lightweight operational security signal (failed logins, rate-limit hits).

    Distinct from AuditLog: these are not part of the cryptographic chain --
    they feed the Security Center's live authentication/suspicious-activity
    feed without being treated as chained financial/administrative events.
    """

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
