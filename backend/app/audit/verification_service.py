from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.audit.hash_chain import GENESIS_HASH, compute_hash
from app.models.audit_log import AuditLog


@dataclass
class VerificationResult:
    status: str  # "VALID" | "COMPROMISED"
    records_checked: int
    broken_links: int
    affected_record: int | None
    affected_records: list[int] = field(default_factory=list)
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def verify_chain(db: Session) -> VerificationResult:
    """Walk the entire global ledger from genesis, recomputing each hash from
    the stored fields and checking the previous_hash linkage. Any record
    whose stored current_hash doesn't match its recomputed hash, or whose
    stored previous_hash doesn't match the prior record's stored hash, is
    reported as an affected record.
    """
    records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()

    expected_previous_hash = GENESIS_HASH
    broken_ids: list[int] = []

    for record in records:
        record_broken = False

        if record.previous_hash != expected_previous_hash:
            record_broken = True

        recomputed_hash = compute_hash(
            event_type=record.event_type,
            actor_id=record.actor_id,
            entity_id=record.entity_id,
            timestamp=record.timestamp,
            canonical_event_data=record.event_data,
            previous_hash=record.previous_hash,
        )
        if recomputed_hash != record.current_hash:
            record_broken = True

        if record_broken:
            broken_ids.append(record.id)

        # Continue the walk from this record's stored hash (not the
        # recomputed one) so a single tampered record is reported once,
        # instead of cascading a false "broken link" onto every record
        # after it.
        expected_previous_hash = record.current_hash

    status = "VALID" if not broken_ids else "COMPROMISED"
    return VerificationResult(
        status=status,
        records_checked=len(records),
        broken_links=len(broken_ids),
        affected_record=broken_ids[0] if broken_ids else None,
        affected_records=broken_ids,
    )
