import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.security.rate_limit import limiter

limiter.enabled = False

DEFAULT_PASSWORD = "Password123"


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def register_user(client: TestClient, email: str, full_name: str = "Test User", password: str = DEFAULT_PASSWORD) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token_response: dict) -> dict:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


def create_trip(client: TestClient, owner_headers: dict, name: str = "Goa Trip", **kwargs) -> dict:
    payload = {"name": name, "currency": "INR"}
    payload.update(kwargs)
    response = client.post("/api/trips", json=payload, headers=owner_headers)
    assert response.status_code == 201, response.text
    return response.json()


def add_member(client: TestClient, owner_headers: dict, trip_id: int, email: str, role: str = "MEMBER") -> dict:
    response = client.post(
        f"/api/trips/{trip_id}/members", json={"email": email, "role": role}, headers=owner_headers
    )
    assert response.status_code == 201, response.text
    return response.json()
