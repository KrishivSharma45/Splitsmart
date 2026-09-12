import hashlib
from datetime import datetime, timezone

GENESIS_HASH = "0" * 64


def _normalize_timestamp(ts: datetime) -> str:
    """Deterministic ISO-8601 string for a timestamp regardless of whether
    it round-tripped through a DB driver that drops tzinfo (e.g. SQLite
    stores naive strings) -- all audit timestamps are always UTC.
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def compute_hash(
    event_type: str,
    actor_id: int | None,
    entity_id: str | None,
    timestamp: datetime,
    canonical_event_data: str,
    previous_hash: str,
) -> str:
    """current_hash = SHA256(event_type | actor_id | entity_id | timestamp |
    canonical_event_data | previous_hash).

    `canonical_event_data` must be the exact canonical-JSON string that is
    persisted on the record (see utils.canonical_json) -- never re-derived
    from a parsed dict, since JSON round-tripping can silently change
    numeric representations (e.g. Decimal -> float) and break the chain.
    """
    parts = [
        event_type,
        str(actor_id) if actor_id is not None else "",
        str(entity_id) if entity_id is not None else "",
        _normalize_timestamp(timestamp),
        canonical_event_data,
        previous_hash,
    ]
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
