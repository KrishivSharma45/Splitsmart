from datetime import datetime

from pydantic import BaseModel

from app.schemas.audit import AuditLogOut


class SecurityEventOut(BaseModel):
    id: int
    event_type: str
    user_id: int | None
    ip_address: str | None
    detail: str | None
    created_at: datetime


class SecurityOverview(BaseModel):
    database_status: str
    audit_chain_status: str
    total_audit_events: int
    last_verification_at: datetime | None
    last_verification_status: str | None
    integrity_violations: int
    recent_security_events: list[SecurityEventOut]
    recent_audit_events: list[AuditLogOut]
    active_users_24h: int
    failed_logins_24h: int
