from tests.conftest import add_member, auth_headers, create_trip, register_user


def test_non_member_cannot_view_trip(client):
    owner = register_user(client, "owner1@example.com", "Owner")
    outsider = register_user(client, "outsider1@example.com", "Outsider")
    trip = create_trip(client, auth_headers(owner))

    response = client.get(f"/api/trips/{trip['id']}", headers=auth_headers(outsider))
    assert response.status_code == 403


def test_member_cannot_update_trip_details(client):
    owner = register_user(client, "owner2@example.com", "Owner")
    member = register_user(client, "member2@example.com", "Member")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "member2@example.com")

    response = client.put(
        f"/api/trips/{trip['id']}",
        json={"name": "Renamed by member"},
        headers=auth_headers(member),
    )
    assert response.status_code == 403


def test_owner_can_update_trip_details(client):
    owner = register_user(client, "owner3@example.com", "Owner")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)

    response = client.put(f"/api/trips/{trip['id']}", json={"name": "Renamed"}, headers=owner_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_member_cannot_add_members(client):
    owner = register_user(client, "owner4@example.com", "Owner")
    member = register_user(client, "member4@example.com", "Member")
    stranger = register_user(client, "stranger4@example.com", "Stranger")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "member4@example.com")

    response = client.post(
        f"/api/trips/{trip['id']}/members",
        json={"email": "stranger4@example.com", "role": "MEMBER"},
        headers=auth_headers(member),
    )
    assert response.status_code == 403


def test_admin_can_add_members(client):
    owner = register_user(client, "owner5@example.com", "Owner")
    admin = register_user(client, "admin5@example.com", "Admin")
    stranger = register_user(client, "stranger5@example.com", "Stranger")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "admin5@example.com", role="ADMIN")

    response = client.post(
        f"/api/trips/{trip['id']}/members",
        json={"email": "stranger5@example.com", "role": "MEMBER"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 201


def test_cannot_remove_the_only_owner(client):
    owner = register_user(client, "owner6@example.com", "Owner")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)

    response = client.delete(f"/api/trips/{trip['id']}/members/{owner['user']['id']}", headers=owner_headers)
    assert response.status_code == 409


def test_member_can_leave_trip_voluntarily(client):
    owner = register_user(client, "owner7@example.com", "Owner")
    member = register_user(client, "member7@example.com", "Member")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "member7@example.com")

    response = client.delete(
        f"/api/trips/{trip['id']}/members/{member['user']['id']}", headers=auth_headers(member)
    )
    assert response.status_code == 204


def test_member_cannot_remove_another_member(client):
    owner = register_user(client, "owner8@example.com", "Owner")
    member_a = register_user(client, "membera8@example.com", "Member A")
    member_b = register_user(client, "memberb8@example.com", "Member B")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "membera8@example.com")
    add_member(client, owner_headers, trip["id"], "memberb8@example.com")

    response = client.delete(
        f"/api/trips/{trip['id']}/members/{member_b['user']['id']}", headers=auth_headers(member_a)
    )
    assert response.status_code == 403


def test_non_owner_cannot_promote_to_owner(client):
    owner = register_user(client, "owner9@example.com", "Owner")
    admin = register_user(client, "admin9@example.com", "Admin")
    member = register_user(client, "member9@example.com", "Member")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "admin9@example.com", role="ADMIN")
    add_member(client, owner_headers, trip["id"], "member9@example.com")

    response = client.patch(
        f"/api/trips/{trip['id']}/members/{member['user']['id']}",
        json={"role": "OWNER"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 403


def test_expense_creator_can_edit_own_expense(client):
    owner = register_user(client, "owner10@example.com", "Owner")
    member = register_user(client, "member10@example.com", "Member")
    owner_headers = auth_headers(owner)
    member_headers = auth_headers(member)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "member10@example.com")

    create_response = client.post(
        f"/api/trips/{trip['id']}/expenses",
        json={
            "description": "Snacks",
            "amount": "100",
            "paid_by": member["user"]["id"],
            "category": "FOOD",
            "split_method": "EQUAL",
            "date": "2026-01-01",
            "participants": [{"user_id": member["user"]["id"]}],
        },
        headers=member_headers,
    )
    expense_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/expenses/{expense_id}",
        json={"description": "Snacks and drinks"},
        headers=member_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Snacks and drinks"


def test_member_cannot_edit_others_expense(client):
    owner = register_user(client, "owner11@example.com", "Owner")
    member_a = register_user(client, "membera11@example.com", "Member A")
    member_b = register_user(client, "memberb11@example.com", "Member B")
    owner_headers = auth_headers(owner)
    trip = create_trip(client, owner_headers)
    add_member(client, owner_headers, trip["id"], "membera11@example.com")
    add_member(client, owner_headers, trip["id"], "memberb11@example.com")

    create_response = client.post(
        f"/api/trips/{trip['id']}/expenses",
        json={
            "description": "Snacks",
            "amount": "100",
            "paid_by": member_a["user"]["id"],
            "category": "FOOD",
            "split_method": "EQUAL",
            "date": "2026-01-01",
            "participants": [{"user_id": member_a["user"]["id"]}],
        },
        headers=auth_headers(member_a),
    )
    expense_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/expenses/{expense_id}",
        json={"description": "Hijacked"},
        headers=auth_headers(member_b),
    )
    assert update_response.status_code == 403
