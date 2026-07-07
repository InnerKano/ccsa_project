"""Pydantic contracts for auth endpoints — see docs/API.md."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.modules.auth.password_policy import MAX_LENGTH, MIN_LENGTH, validate_password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)

    @model_validator(mode="after")
    def check_password_strength(self) -> "RegisterRequest":
        # Authoritative strength gate (NIST-aligned, D24) with email context so a
        # password containing the address is rejected. The frontend mirrors these
        # rules for live feedback, but the server is the source of truth.
        validate_password(self.password, self.email)
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        # Reset has no email context in the body; enforce the rest of the policy.
        validate_password(value)
        return value


class RegisterResponse(BaseModel):
    id: UUID
    email: EmailStr
    token: str


class TokenResponse(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str
