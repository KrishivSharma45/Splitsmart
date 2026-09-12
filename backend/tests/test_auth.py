from tests.conftest import auth_headers, register_user


def test_register_creates_user_and_returns_token(client):
    data = register_user(client, "alice@example.com", "Alice Doe")
    assert data["user"]["email"] == "alice@example.com"
    assert "access_token" in data


def test_register_rejects_duplicate_email(client):
    register_user(client, "bob@example.com")
    response = client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "full_name": "Bob Two", "password": "Password123"},
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "full_name": "Weak Pw", "password": "abc"},
    )
    assert response.status_code == 422


def test_login_success(client):
    register_user(client, "carol@example.com")
    response = client.post("/api/auth/login", json={"email": "carol@example.com", "password": "Password123"})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "carol@example.com"


def test_login_wrong_password_returns_401(client):
    register_user(client, "dave@example.com")
    response = client.post("/api/auth/login", json={"email": "dave@example.com", "password": "WrongPassword1"})
    assert response.status_code == 401


def test_protected_route_requires_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_returns_current_user(client):
    data = register_user(client, "erin@example.com", "Erin Example")
    response = client.get("/api/auth/me", headers=auth_headers(data))
    assert response.status_code == 200
    assert response.json()["email"] == "erin@example.com"


def test_invalid_token_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_change_password_flow(client):
    data = register_user(client, "frank@example.com")
    headers = auth_headers(data)

    wrong = client.post(
        "/api/auth/change-password",
        json={"current_password": "WrongOld1", "new_password": "NewPassword1"},
        headers=headers,
    )
    assert wrong.status_code == 400

    ok = client.post(
        "/api/auth/change-password",
        json={"current_password": "Password123", "new_password": "NewPassword1"},
        headers=headers,
    )
    assert ok.status_code == 204

    old_login = client.post("/api/auth/login", json={"email": "frank@example.com", "password": "Password123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"email": "frank@example.com", "password": "NewPassword1"})
    assert new_login.status_code == 200
