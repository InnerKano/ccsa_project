"""Auth API happy-path and error tests."""

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_register_returns_user_and_token(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert "id" in body
    assert isinstance(body["token"], str) and len(body["token"]) > 0


def test_register_normalizes_email_to_lowercase(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "MixedCase@Example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "mixedcase@example.com"


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    payload = {"email": "duplicate@example.com", "password": "securepassword123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_returns_token(client: TestClient) -> None:
    email = "loginuser@example.com"
    password = "securepassword123"
    client.post("/api/auth/register", json={"email": email, "password": password})

    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["token"], str) and len(body["token"]) > 0


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    email = "wrongpass@example.com"
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
