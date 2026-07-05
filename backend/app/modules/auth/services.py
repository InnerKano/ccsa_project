"""Auth business logic: register, authenticate."""

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User


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
