import json

from app.audit.verification_service import verify_chain
from app.models.audit_log import AuditLog
from tests.conftest import auth_headers, create_trip, register_user


def test_tampering_with_event_data_is_detected(client, db_session):
    krishiv = register_user(client, "tamper@example.com", "Krishiv")
    headers = auth_headers(krishiv)
    trip = create_trip(client, headers, name="Tamper Trip")

    expense_response = client.post(
        f"/api/trips/{trip['id']}/expenses",
        json={
            "description": "Hotel",
            "amount": "8000",
            "paid_by": krishiv["user"]["id"],
            "category": "ACCOMMODATION",
            "split_method": "EQUAL",
            "date": "2026-01-01",
            "participants": [{"user_id": krishiv["user"]["id"]}],
        },
        headers=headers,
    )
    assert expense_response.status_code == 201

    # Sanity check: the untampered chain must verify as VALID first.
    clean_result = verify_chain(db_session)
    assert clean_result.status == "VALID"

    # Directly mutate a record's event_data via the DB session, bypassing
    # audit_service.record_event entirely -- simulating an attacker (or a
    # bug) that edits history straight in the database.
    target = db_session.query(AuditLog).filter(AuditLog.event_type == "EXPENSE_CREATED").first()
    assert target is not None
    tampered_data = json.loads(target.event_data)
    tampered_data["amount"] = "1.00"  # attacker tries to shrink the recorded expense
    target.event_data = json.dumps(tampered_data)
    db_session.commit()

    result = verify_chain(db_session)
    assert result.status == "COMPROMISED"
    assert result.broken_links >= 1
    assert result.affected_record == target.id
    assert target.id in result.affected_records


def test_tampering_detected_via_api_endpoint(client, db_session):
    krishiv = register_user(client, "tamper2@example.com", "Krishiv")
    headers = auth_headers(krishiv)
    trip = create_trip(client, headers, name="Tamper Trip 2")

    target = db_session.query(AuditLog).filter(AuditLog.event_type == "TRIP_CREATED").first()
    assert target is not None
    target.current_hash = "0" * 64  # corrupt the stored hash directly
    db_session.commit()

    response = client.post(f"/api/trips/{trip['id']}/audit/verify", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPROMISED"
    assert body["broken_links"] >= 1


def test_deleting_a_record_breaks_the_chain_link(client, db_session):
    krishiv = register_user(client, "tamper3@example.com", "Krishiv")
    headers = auth_headers(krishiv)
    create_trip(client, headers, name="Tamper Trip 3")

    records = db_session.query(AuditLog).order_by(AuditLog.id.asc()).all()
    assert len(records) >= 2
    middle_record = records[0]  # USER_REGISTERED, the first record
    db_session.delete(middle_record)
    db_session.commit()

    result = verify_chain(db_session)
    assert result.status == "COMPROMISED"
