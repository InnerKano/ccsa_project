"""Password recovery + password-policy tests.

Recovery uses a stateless JWT bound to the user's password hash (D23), so these
tests mint a valid token via the security helper (the forgot endpoint never
returns the token — that would leak it and defeat email delivery).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_password_reset_token
from app.modules.auth.models import User

pytestmark = pytest.mark.integration


def _unique_email(prefix: str = "reset") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register(client: TestClient, email: str, password: str = "correct horse battery") -> None:
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201


def _reset_token_for(db_session: Session, email: str) -> str:
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    return create_password_reset_token(user.id, user.password_hash)


# --- forgot-password: no user enumeration ------------------------------------


def test_forgot_password_unknown_email_returns_generic_200(client: TestClient) -> None:
    response = client.post(
        "/api/auth/forgot-password", json={"email": _unique_email("ghost")}
    )
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]


def test_forgot_password_known_email_returns_same_message(client: TestClient) -> None:
    email = _unique_email("known")
    _register(client, email)
    response = client.post("/api/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["message"]


# --- reset-password happy path + single use ----------------------------------


def test_reset_password_changes_password(client: TestClient, db_session: Session) -> None:
    email = _unique_email("change")
    old_password = "correct horse battery"
    new_password = "brand new passphrase 7"
    _register(client, email, old_password)
    token = _reset_token_for(db_session, email)

    response = client.post(
        "/api/auth/reset-password", json={"token": token, "password": new_password}
    )
    assert response.status_code == 200

    assert client.post(
        "/api/auth/login", json={"email": email, "password": new_password}
    ).status_code == 200
    assert client.post(
        "/api/auth/login", json={"email": email, "password": old_password}
    ).status_code == 401


def test_reset_token_is_single_use(client: TestClient, db_session: Session) -> None:
    email = _unique_email("single")
    _register(client, email)
    token = _reset_token_for(db_session, email)

    first = client.post(
        "/api/auth/reset-password", json={"token": token, "password": "first passphrase 9"}
    )
    assert first.status_code == 200

    # The same token no longer validates — the password hash it was signed
    # against has changed (D23 self-invalidation).
    second = client.post(
        "/api/auth/reset-password", json={"token": token, "password": "second passphrase 9"}
    )
    assert second.status_code == 400
    assert second.json()["detail"] == "Invalid or expired reset link"


def test_reset_password_rejects_garbage_token(client: TestClient) -> None:
    response = client.post(
        "/api/auth/reset-password",
        json={"token": "not-a-jwt", "password": "brand new passphrase 7"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset link"


def test_reset_password_weak_password_rejected(client: TestClient, db_session: Session) -> None:
    email = _unique_email("weak")
    _register(client, email)
    token = _reset_token_for(db_session, email)
    response = client.post(
        "/api/auth/reset-password", json={"token": token, "password": "password123"}
    )
    assert response.status_code == 422


# --- password policy at register ---------------------------------------------


def test_register_rejects_common_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": _unique_email("common"), "password": "password123"},
    )
    assert response.status_code == 422


def test_register_rejects_password_containing_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "janedoe@example.com", "password": "janedoe-secret"},
    )
    assert response.status_code == 422


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": _unique_email("short"), "password": "short"},
    )
    assert response.status_code == 422
