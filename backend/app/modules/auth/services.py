"""Auth business logic: register, authenticate, password recovery."""

import logging
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    hash_password,
    read_reset_token_subject,
    verify_password,
    verify_password_reset_token,
)
from app.modules.auth.models import User
from app.shared.email.factory import get_email_sender

logger = logging.getLogger("ccsa.auth")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    normalized = normalize_email(email)
    existing = db.query(User).filter(User.email == normalized).first()
    if existing is not None:
        raise ValueError("Email already registered")

    user = User(email=normalized, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_access_token(user.id)


def authenticate_user(db: Session, email: str, password: str) -> str:
    normalized = normalize_email(email)
    user = db.query(User).filter(User.email == normalized).first()
    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return create_access_token(user.id)


def _build_reset_link(token: str) -> str:
    query = urlencode({"token": token})
    return f"{settings.frontend_url.rstrip('/')}/reset-password?{query}"


def _send_reset_email(user: User, token: str) -> None:
    link = _build_reset_link(token)
    minutes = settings.password_reset_expire_minutes
    subject = "Reset your CCSA password"
    text_body = (
        "We received a request to reset your CCSA password.\n\n"
        f"Reset it here (link valid for {minutes} minutes):\n{link}\n\n"
        "If you did not request this, you can ignore this email — your password "
        "will not change."
    )
    html_body = (
        "<p>We received a request to reset your CCSA password.</p>"
        f'<p><a href="{link}">Reset your password</a> '
        f"(link valid for {minutes} minutes).</p>"
        "<p>If you did not request this, you can ignore this email — your "
        "password will not change.</p>"
    )
    get_email_sender().send(
        to=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


def request_password_reset(db: Session, email: str) -> None:
    """Start the recovery flow.

    Intentionally returns nothing and never signals whether the email exists, so
    the endpoint response is identical either way (no user enumeration, D23).
    Transport failures are swallowed and logged (never re-raised) so a delivery
    error on an existing account does not produce a 500 that would distinguish it
    from an unknown email — the response must be indistinguishable in all cases.
    The log message never includes the token or link.
    """
    normalized = normalize_email(email)
    user = db.query(User).filter(User.email == normalized).first()
    if user is None:
        return
    token = create_password_reset_token(user.id, user.password_hash)
    try:
        _send_reset_email(user, token)
    except Exception:  # noqa: BLE001 — never leak existence via an error response
        logger.exception("Failed to send password reset email")


def reset_password(db: Session, token: str, new_password: str) -> None:
    """Consume a reset token and set a new password.

    The token is single-use by construction (D23): it is signed with a key
    derived from the current password hash, so changing the password invalidates
    this token and any other outstanding one for the user. Failures raise a
    generic ValueError — the caller must not reveal whether the token was
    malformed, expired, or for a missing user.
    """
    user_id = read_reset_token_subject(token)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not verify_password_reset_token(token, user.password_hash):
        raise ValueError("Invalid or expired reset link")

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
