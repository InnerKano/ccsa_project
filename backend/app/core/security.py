"""Cross-cutting security: password hashing, JWT, and current-user dependency."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.models import User

bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

# Purpose claim that distinguishes a single-use password-reset token from a
# normal access token — a reset token must never be accepted as a login (D23).
RESET_TOKEN_PURPOSE = "pwd_reset"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def _reset_signing_key(password_hash: str) -> str:
    """Derive the reset-token signing key from the secret + the user's current
    password hash.

    Binding the signature to `password_hash` makes reset tokens **single-use and
    self-invalidating without server-side state** (D23): the moment the password
    changes (a successful reset, or any other change), the hash changes, so every
    outstanding reset token for that user stops validating. The bcrypt hash also
    embeds a per-user salt, so a token for one user can never validate for
    another. No DB table or migration is needed.
    """
    return f"{settings.secret_key}:{password_hash}"


def create_password_reset_token(user_id: UUID, password_hash: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )
    payload = {"sub": str(user_id), "purpose": RESET_TOKEN_PURPOSE, "exp": expire}
    return jwt.encode(payload, _reset_signing_key(password_hash), algorithm=ALGORITHM)


def read_reset_token_subject(token: str) -> UUID | None:
    """Return the subject (user id) from an *unverified* reset token, or None.

    The signature can only be checked once we know the user (their password hash
    is part of the key), so we first read the claims without verifying to learn
    who the token is for, then verify separately in `verify_password_reset_token`.
    """
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError:
        return None
    if claims.get("purpose") != RESET_TOKEN_PURPOSE:
        return None
    subject = claims.get("sub")
    if subject is None:
        return None
    try:
        return UUID(subject)
    except (ValueError, TypeError):
        return None


def verify_password_reset_token(token: str, password_hash: str) -> bool:
    """Fully validate a reset token (signature + expiry + purpose) against the
    user's current password hash."""
    try:
        payload = jwt.decode(
            token, _reset_signing_key(password_hash), algorithms=[ALGORITHM]
        )
    except JWTError:
        return False
    return payload.get("purpose") == RESET_TOKEN_PURPOSE


def _user_id_from_token(token: str) -> UUID:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("missing subject")
    return UUID(subject)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        user_id = _user_id_from_token(credentials.credentials)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user
