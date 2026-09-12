from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.audit.hash_chain import GENESIS_HASH, compute_hash
from app.models.audit_log import AuditLog
from app.utils.canonical_json import canonical_json


def record_event(
    db: Session,
    event_type: str,
    entity_type: str,
    actor_id: int | None = None,
    trip_id: int | None = None,
    entity_id: int | str | None = None,
    event_data: dict | None = None,
) -> AuditLog:
    """Append one event to the global audit ledger.

    Must run inside the same DB transaction/session as the business action
    it documents. SQLite serializes writers at the connection level, so the
    "read last hash, compute next hash, insert" sequence below is safe for
    the dev DB; a Postgres deployment should additionally take a row lock
    (e.g. `SELECT ... FOR UPDATE` on a sentinel row) around this call to
    prevent a lost-update race between concurrent appenders.
    """
    event_data = event_data or {}
    canonical_data = canonical_json(event_data)
    timestamp = datetime.now(timezone.utc)

    last_record = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_record.current_hash if last_record else GENESIS_HASH

    entity_id_str = str(entity_id) if entity_id is not None else None
    current_hash = compute_hash(
        event_type=event_type,
        actor_id=actor_id,
        entity_id=entity_id_str,
        timestamp=timestamp,
        canonical_event_data=canonical_data,
        previous_hash=previous_hash,
    )

    record = AuditLog(
        event_type=event_type,
        actor_id=actor_id,
        trip_id=trip_id,
        entity_type=entity_type,
        entity_id=entity_id_str,
        event_data=canonical_data,
        timestamp=timestamp,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(record)
    db.flush()
    return record
