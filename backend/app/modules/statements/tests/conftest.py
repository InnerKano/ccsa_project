"""DB-backed test fixtures for statements module tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.main import app

FIXTURES_DIR = Path(__file__).resolve().parents[4] / "fixtures"
SAMPLE_CSV = FIXTURES_DIR / "sample.csv"


def _postgres_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = inspect(connection).get_table_names()
            if "statements" not in tables or "transactions" not in tables:
                return False
    except Exception:
        return False
    return True


@pytest.fixture(scope="session", autouse=True)
def require_postgres() -> None:
    if not _postgres_ready():
        pytest.skip(
            "Postgres with statements migration required — use docker compose + alembic upgrade head"
        )


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"email": "statements-user@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"email": "other-user@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}
