from tests.conftest import add_member, auth_headers, create_trip, register_user


def _setup_goa_trip(client):
    krishiv = register_user(client, "krishiv@example.com", "Krishiv")
    rahul = register_user(client, "rahul@example.com", "Rahul")
    arjun = register_user(client, "arjun@example.com", "Arjun")
    aditya = register_user(client, "aditya@example.com", "Aditya")

    k_headers = auth_headers(krishiv)
    trip = create_trip(client, k_headers, name="Goa Trip")
    add_member(client, k_headers, trip["id"], "rahul@example.com")
    add_member(client, k_headers, trip["id"], "arjun@example.com")
    add_member(client, k_headers, trip["id"], "aditya@example.com")

    return {
        "trip": trip,
        "k_headers": k_headers,
        "krishiv": krishiv["user"],
        "rahul": rahul["user"],
        "arjun": arjun["user"],
        "aditya": aditya["user"],
    }


def test_equal_split_matches_spec_worked_example(client):
    ctx = _setup_goa_trip(client)
    trip_id = ctx["trip"]["id"]
    user_ids = [ctx["krishiv"]["id"], ctx["rahul"]["id"], ctx["arjun"]["id"], ctx["aditya"]["id"]]

    response = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={
            "description": "Hotel",
            "amount": "8000",
            "paid_by": ctx["krishiv"]["id"],
            "category": "ACCOMMODATION",
            "split_method": "EQUAL",
            "date": "2026-01-01",
            "participants": [{"user_id": uid} for uid in user_ids],
        },
        headers=ctx["k_headers"],
    )
    assert response.status_code == 201, response.text

    balances_response = client.get(f"/api/trips/{trip_id}/balances", headers=ctx["k_headers"])
    assert balances_response.status_code == 200
    balances = {b["user"]["id"]: b for b in balances_response.json()["balances"]}

    assert balances[ctx["krishiv"]["id"]]["net_balance"] == "6000.00"
    assert balances[ctx["rahul"]["id"]]["net_balance"] == "-2000.00"
    assert balances[ctx["arjun"]["id"]]["net_balance"] == "-2000.00"
    assert balances[ctx["aditya"]["id"]]["net_balance"] == "-2000.00"

    debts_response = client.get(f"/api/trips/{trip_id}/debts", headers=ctx["k_headers"])
    assert debts_response.status_code == 200
    debts = debts_response.json()["simplified_debts"]
    assert len(debts) == 3
    for edge in debts:
        assert edge["to_user"]["id"] == ctx["krishiv"]["id"]
        assert edge["amount"] == "2000.00"


def test_settlement_reduces_balance(client):
    ctx = _setup_goa_trip(client)
    trip_id = ctx["trip"]["id"]
    user_ids = [ctx["krishiv"]["id"], ctx["rahul"]["id"]]

    client.post(
        f"/api/trips/{trip_id}/expenses",
        json={
            "description": "Lunch",
            "amount": "1000",
            "paid_by": ctx["krishiv"]["id"],
            "category": "FOOD",
            "split_method": "EQUAL",
            "date": "2026-01-02",
            "participants": [{"user_id": uid} for uid in user_ids],
        },
        headers=ctx["k_headers"],
    )

    settle_response = client.post(
        f"/api/trips/{trip_id}/settlements",
        json={
            "payer_id": ctx["rahul"]["id"],
            "receiver_id": ctx["krishiv"]["id"],
            "amount": "500",
            "date": "2026-01-03",
        },
        headers=ctx["k_headers"],
    )
    assert settle_response.status_code == 201, settle_response.text

    balances_response = client.get(f"/api/trips/{trip_id}/balances", headers=ctx["k_headers"])
    balances = {b["user"]["id"]: b for b in balances_response.json()["balances"]}
    assert balances[ctx["rahul"]["id"]]["net_balance"] == "0.00"
    assert balances[ctx["krishiv"]["id"]]["net_balance"] == "0.00"


def test_voided_expense_excluded_from_balances(client):
    ctx = _setup_goa_trip(client)
    trip_id = ctx["trip"]["id"]
    user_ids = [ctx["krishiv"]["id"], ctx["rahul"]["id"]]

    create_response = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={
            "description": "Taxi",
            "amount": "500",
            "paid_by": ctx["krishiv"]["id"],
            "category": "TRANSPORT",
            "split_method": "EQUAL",
            "date": "2026-01-02",
            "participants": [{"user_id": uid} for uid in user_ids],
        },
        headers=ctx["k_headers"],
    )
    expense_id = create_response.json()["id"]

    void_response = client.post(
        f"/api/expenses/{expense_id}/void", json={"reason": "duplicate entry"}, headers=ctx["k_headers"]
    )
    assert void_response.status_code == 200
    assert void_response.json()["status"] == "VOIDED"

    balances_response = client.get(f"/api/trips/{trip_id}/balances", headers=ctx["k_headers"])
    balances = {b["user"]["id"]: b for b in balances_response.json()["balances"]}
    assert balances[ctx["krishiv"]["id"]]["net_balance"] == "0.00"
    assert balances[ctx["rahul"]["id"]]["net_balance"] == "0.00"


def test_percentage_split_validation_rejects_non_100_total(client):
    ctx = _setup_goa_trip(client)
    trip_id = ctx["trip"]["id"]

    response = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={
            "description": "Bad split",
            "amount": "1000",
            "paid_by": ctx["krishiv"]["id"],
            "category": "OTHER",
            "split_method": "PERCENTAGE",
            "date": "2026-01-02",
            "participants": [
                {"user_id": ctx["krishiv"]["id"], "percentage": "50"},
                {"user_id": ctx["rahul"]["id"], "percentage": "40"},
            ],
        },
        headers=ctx["k_headers"],
    )
    assert response.status_code == 400


def test_expense_rejects_non_member_participant(client):
    ctx = _setup_goa_trip(client)
    trip_id = ctx["trip"]["id"]
    outsider = register_user(client, "outsider@example.com", "Outsider")

    response = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={
            "description": "Sneaky",
            "amount": "100",
            "paid_by": ctx["krishiv"]["id"],
            "category": "OTHER",
            "split_method": "EQUAL",
            "date": "2026-01-02",
            "participants": [{"user_id": ctx["krishiv"]["id"]}, {"user_id": outsider["user"]["id"]}],
        },
        headers=ctx["k_headers"],
    )
    assert response.status_code == 400
