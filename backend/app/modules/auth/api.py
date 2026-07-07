"""Auth HTTP routes — register, login, and password recovery."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.modules.auth.services import (
    authenticate_user,
    register_user,
    request_password_reset,
    reset_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Same copy whether or not the email exists — prevents account enumeration (D23).
_FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, a password reset link has been sent."
)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    try:
        user, token = register_user(db, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return RegisterResponse(id=user.id, email=user.email, token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token = authenticate_user(db, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return TokenResponse(token=token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    body: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    request_password_reset(db, body.email)
    return MessageResponse(message=_FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password_endpoint(
    body: ResetPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    try:
        reset_password(db, body.token, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return MessageResponse(message="Your password has been reset. You can now sign in.")
