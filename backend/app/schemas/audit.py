from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.user import UserSummary


class AuditLogOut(BaseModel):
    id: int
    event_type: str
    actor: UserSummary | None
    trip_id: int | None
    entity_type: str
    entity_id: str | None
    event_data: dict[str, Any]
    timestamp: datetime
    previous_hash: str
    current_hash: str


class AuditVerifyResponse(BaseModel):
    status: str
    records_checked: int
    broken_links: int
    affected_record: int | None
    affected_records: list[int]
    verified_at: datetime
    scope: str = "global_ledger"
