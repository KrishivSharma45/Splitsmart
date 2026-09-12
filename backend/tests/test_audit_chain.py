from datetime import datetime, timezone

from app.audit.hash_chain import GENESIS_HASH, compute_hash
from tests.conftest import auth_headers, create_trip, register_user


def test_compute_hash_is_deterministic():
    ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    h1 = compute_hash("EXPENSE_CREATED", 1, "42", ts, '{"amount":"100.00"}', GENESIS_HASH)
    h2 = compute_hash("EXPENSE_CREATED", 1, "42", ts, '{"amount":"100.00"}', GENESIS_HASH)
    assert h1 == h2
    assert len(h1) == 64


def test_compute_hash_changes_with_any_input():
    ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    base = compute_hash("EXPENSE_CREATED", 1, "42", ts, '{"amount":"100.00"}', GENESIS_HASH)

    assert compute_hash("EXPENSE_UPDATED", 1, "42", ts, '{"amount":"100.00"}', GENESIS_HASH) != base
    assert compute_hash("EXPENSE_CREATED", 2, "42", ts, '{"amount":"100.00"}', GENESIS_HASH) != base
    assert compute_hash("EXPENSE_CREATED", 1, "43", ts, '{"amount":"100.00"}', GENESIS_HASH) != base
    assert compute_hash("EXPENSE_CREATED", 1, "42", ts, '{"amount":"200.00"}', GENESIS_HASH) != base
    assert compute_hash("EXPENSE_CREATED", 1, "42", ts, '{"amount":"100.00"}', "a" * 64) != base


def test_verification_reports_valid_for_untampered_chain(client):
    krishiv = register_user(client, "krishiv2@example.com", "Krishiv")
    headers = auth_headers(krishiv)
    trip = create_trip(client, headers, name="Manali Trip")

    client.post(
        f"/api/trips/{trip['id']}/expenses",
        json={
            "description": "Snacks",
            "amount": "200",
            "paid_by": krishiv["user"]["id"],
            "category": "FOOD",
            "split_method": "EQUAL",
            "date": "2026-01-01",
            "participants": [{"user_id": krishiv["user"]["id"]}],
        },
        headers=headers,
    )

    response = client.post(f"/api/trips/{trip['id']}/audit/verify", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "VALID"
    assert body["broken_links"] == 0
    assert body["affected_record"] is None
    assert body["records_checked"] >= 3  # USER_REGISTERED, TRIP_CREATED, EXPENSE_CREATED


def test_trip_audit_log_lists_expected_events(client):
    krishiv = register_user(client, "krishiv3@example.com", "Krishiv")
    headers = auth_headers(krishiv)
    trip = create_trip(client, headers, name="Kerala Trip")

    response = client.get(f"/api/trips/{trip['id']}/audit", headers=headers)
    assert response.status_code == 200
    event_types = {r["event_type"] for r in response.json()}
    assert "TRIP_CREATED" in event_types
