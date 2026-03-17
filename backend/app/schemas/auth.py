from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class ResendVerificationRequest(BaseModel):
    email: EmailStr | None = None


class UsageSummary(BaseModel):
    month_start: datetime
    jobs_used: int
    jobs_limit: int | None
    jobs_remaining: int | None


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    plan_key: str
    email_verified: bool
    email_verified_at: datetime | None = None
    created_at: datetime


class AuthSessionResponse(BaseModel):
    user: AuthUser
    usage: UsageSummary
    message: str | None = None
    requires_email_verification: bool = False
    mail_preview_url: str | None = None


class ActionStatusResponse(BaseModel):
    success: bool = True
    message: str
    mail_preview_url: str | None = None


class DevMailMessage(BaseModel):
    id: str
    kind: str
    to_email: EmailStr
    subject: str
    preview_url: str
    action_url: str | None = None
    created_at: datetime
