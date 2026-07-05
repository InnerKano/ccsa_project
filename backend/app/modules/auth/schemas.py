"""Pydantic contracts for auth endpoints — see docs/API.md."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterResponse(BaseModel):
    id: UUID
    email: EmailStr
    token: str


class TokenResponse(BaseModel):
    token: str
