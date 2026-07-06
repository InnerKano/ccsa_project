"""Auth API happy-path and error tests.

Emails are randomized per test so the suite never depends on a clean database
(complements the transaction-rollback isolation in conftest.py).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def test_register_returns_user_and_token(client: TestClient) -> None:
    email = _unique_email("newuser")
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "securepassword123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert "id" in body
    assert isinstance(body["token"], str) and len(body["token"]) > 0


def test_register_normalizes_email_to_lowercase(client: TestClient) -> None:
    token = uuid4().hex
    response = client.post(
        "/api/auth/register",
        json={"email": f"MixedCase-{token}@Example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == f"mixedcase-{token}@example.com"


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    payload = {"email": _unique_email("duplicate"), "password": "securepassword123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_returns_token(client: TestClient) -> None:
    email = _unique_email("loginuser")
    password = "securepassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})

    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["token"], str) and len(body["token"]) > 0


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    email = _unique_email("wrongpass")
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "securepassword123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
