from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import Depends, HTTPException, Request, Response, status

from app.core.config import settings
from app.core.database import job_repository
from app.core.mail import LocalFileMailProvider, MailMessage, mail_provider
from app.core.plans import get_plan, serialize_plans
from app.core.security import (
    generate_action_token,
    generate_session_token,
    hash_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.schemas.auth import ActionStatusResponse, AuthSessionResponse, AuthUser, UsageSummary

EMAIL_VERIFICATION_TOKEN = "email_verification"
PASSWORD_RESET_TOKEN = "password_reset"


def _month_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _frontend_url(path: str) -> str:
    return f"{settings.app_public_url.rstrip('/')}{path}"


def _exposed_preview_url(preview_url: str | None) -> str | None:
    if settings.app_env.lower() == "production":
        return None
    if not isinstance(mail_provider, LocalFileMailProvider):
        return None
    return preview_url


def _signup_verification_message(preview_url: str | None) -> str:
    if _exposed_preview_url(preview_url):
        return "Your account is ready. Open the local verification preview or check the verify email page to finish setup."
    return "Your account is ready. Check your email for a verification link to finish setting up CreatorLab."


def _resend_verification_message(preview_url: str | None) -> str:
    if _exposed_preview_url(preview_url):
        return "A fresh verification message was saved locally. Open the preview or use the verify email page to continue."
    return "A fresh verification email is on the way."


def _build_usage_summary(user: dict[str, object]) -> UsageSummary:
    month_start = _month_start_utc()
    used = job_repository.get_monthly_usage(str(user["id"]), month_start.isoformat())
    plan = get_plan(str(user["plan_key"]))
    remaining = None if plan.monthly_jobs is None else max(plan.monthly_jobs - used, 0)
    return UsageSummary(
        month_start=month_start,
        jobs_used=used,
        jobs_limit=plan.monthly_jobs,
        jobs_remaining=remaining,
    )


def _build_auth_user(user: dict[str, object]) -> AuthUser:
    return AuthUser(
        id=str(user["id"]),
        email=str(user["email"]),
        full_name=str(user["full_name"]) if user.get("full_name") else None,
        plan_key=str(user["plan_key"]),
        email_verified=bool(user.get("email_verified")),
        email_verified_at=(
            datetime.fromisoformat(str(user["email_verified_at"])) if user.get("email_verified_at") else None
        ),
        created_at=datetime.fromisoformat(str(user["created_at"])),
    )


def serialize_user_session(
    user: dict[str, object],
    *,
    message: str | None = None,
    mail_preview_url: str | None = None,
) -> AuthSessionResponse:
    return AuthSessionResponse(
        user=_build_auth_user(user),
        usage=_build_usage_summary(user),
        message=message,
        requires_email_verification=bool(settings.require_email_verification and not user.get("email_verified")),
        mail_preview_url=mail_preview_url,
    )


def _send_email_verification_email(user: dict[str, object]) -> str | None:
    token = generate_action_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_ttl_hours)
    job_repository.create_auth_token(
        user_id=str(user["id"]),
        token_hash=hash_token(token),
        token_type=EMAIL_VERIFICATION_TOKEN,
        expires_at=expires_at.isoformat(),
        meta={"email": str(user["email"])},
    )
    action_url = _frontend_url(f"/verify-email?token={quote(token, safe='')}")
    message = MailMessage(
        to_email=str(user["email"]),
        subject="Verify your CreatorLab email",
        kind=EMAIL_VERIFICATION_TOKEN,
        action_url=action_url,
        text_body=(
            "Welcome to CreatorLab.\n\n"
            f"Verify your email by opening this link:\n{action_url}\n\n"
            f"This link expires in {settings.email_verification_ttl_hours} hours."
        ),
        html_body=(
            "<h1>Verify your email</h1>"
            "<p>Welcome to CreatorLab.</p>"
            f"<p><a href=\"{action_url}\">Verify your email address</a></p>"
            f"<p>This link expires in {settings.email_verification_ttl_hours} hours.</p>"
        ),
    )
    return mail_provider.send(message).preview_url


def _send_password_reset_email(user: dict[str, object]) -> str | None:
    token = generate_action_token()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_ttl_minutes)
    job_repository.create_auth_token(
        user_id=str(user["id"]),
        token_hash=hash_token(token),
        token_type=PASSWORD_RESET_TOKEN,
        expires_at=expires_at.isoformat(),
        meta={"email": str(user["email"])},
    )
    action_url = _frontend_url(f"/reset-password?token={quote(token, safe='')}")
    message = MailMessage(
        to_email=str(user["email"]),
        subject="Reset your CreatorLab password",
        kind=PASSWORD_RESET_TOKEN,
        action_url=action_url,
        text_body=(
            "We received a request to reset your CreatorLab password.\n\n"
            f"Reset it here:\n{action_url}\n\n"
            f"This link expires in {settings.password_reset_ttl_minutes} minutes."
        ),
        html_body=(
            "<h1>Reset your password</h1>"
            "<p>We received a request to reset your CreatorLab password.</p>"
            f"<p><a href=\"{action_url}\">Choose a new password</a></p>"
            f"<p>This link expires in {settings.password_reset_ttl_minutes} minutes.</p>"
        ),
    )
    return mail_provider.send(message).preview_url


def sign_up_user(email: str, password: str, full_name: str | None) -> AuthSessionResponse:
    existing = job_repository.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    user = job_repository.create_user(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        plan_key="free",
        email_verified=False,
        email_verified_at=None,
    )
    preview_url = _send_email_verification_email(user)
    return serialize_user_session(
        user,
        message=_signup_verification_message(preview_url),
        mail_preview_url=_exposed_preview_url(preview_url),
    )


def login_user(email: str, password: str) -> AuthSessionResponse:
    user = job_repository.get_user_by_email(email)
    if not user or not verify_password(password, str(user["password_hash"])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="We couldn't sign you in with that email and password.",
        )
    if not bool(user["is_active"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive.")
    if settings.require_email_verification and not bool(user.get("email_verified")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in. You can request a new verification link from the verify email page.",
        )
    return serialize_user_session(user)


def verify_email_token(token: str) -> ActionStatusResponse:
    token_record = job_repository.get_auth_token(hash_token(token), EMAIL_VERIFICATION_TOKEN)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That verification link is invalid or has expired.",
        )
    user = job_repository.mark_user_email_verified(
        user_id=str(token_record["auth_user_id"]),
        verified_at=datetime.now(timezone.utc).isoformat(),
    )
    job_repository.consume_auth_token(str(token_record["auth_token_id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return ActionStatusResponse(message="Your email has been verified. You can continue in CreatorLab.")


def resend_verification_email(email: str | None, user: dict[str, object] | None) -> ActionStatusResponse:
    target_user = user
    if not target_user and email:
        target_user = job_repository.get_user_by_email(email)
    if not target_user:
        return ActionStatusResponse(message="If that account exists, a new verification email is on the way.")
    if not user and bool(target_user.get("email_verified")):
        return ActionStatusResponse(message="If that account exists, a new verification email is on the way.")
    if bool(target_user.get("email_verified")):
        return ActionStatusResponse(message="This email address is already verified.")
    preview_url = _send_email_verification_email(target_user)
    return ActionStatusResponse(
        message=_resend_verification_message(preview_url),
        mail_preview_url=_exposed_preview_url(preview_url),
    )


def request_password_reset(email: str) -> ActionStatusResponse:
    user = job_repository.get_user_by_email(email)
    preview_url: str | None = None
    if user and bool(user["is_active"]):
        preview_url = _send_password_reset_email(user)
    return ActionStatusResponse(
        message=(
            "If an account matches that email, a password reset link has been sent."
            if not _exposed_preview_url(preview_url)
            else "If an account matches that email, a local password reset preview is ready."
        ),
        mail_preview_url=_exposed_preview_url(preview_url),
    )


def reset_password(token: str, password: str) -> ActionStatusResponse:
    token_record = job_repository.get_auth_token(hash_token(token), PASSWORD_RESET_TOKEN)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That password reset link is invalid or has expired.",
        )
    user = job_repository.update_user_password(str(token_record["auth_user_id"]), hash_password(password))
    job_repository.consume_auth_token(str(token_record["auth_token_id"]))
    job_repository.delete_sessions_for_user(str(token_record["auth_user_id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return ActionStatusResponse(message="Your password has been reset. Please sign in with your new password.")


def issue_session_cookie(response: Response, user_id: str) -> None:
    token = generate_session_token()
    token_hash = hash_session_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)
    job_repository.create_session(user_id=user_id, token_hash=token_hash, expires_at=expires_at.isoformat())
    secure_cookie = settings.session_cookie_secure or settings.app_env.lower() == "production"
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        domain=settings.cookie_domain,
        path="/",
    )


def clear_session_cookie(request: Request, response: Response) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        job_repository.delete_session(hash_session_token(token))
    response.delete_cookie(
        key=settings.session_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )


def get_optional_current_user(request: Request) -> dict[str, object] | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    return job_repository.get_user_by_session_token(hash_session_token(token))


def get_current_user(
    request: Request,
    user: dict[str, object] | None = Depends(get_optional_current_user),
) -> dict[str, object]:
    if not user:
        if request.cookies.get(settings.session_cookie_name):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please sign in again.",
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return user


def enforce_verified_email(user: dict[str, object]) -> None:
    if settings.require_email_verification and not bool(user.get("email_verified")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email before starting new jobs.",
        )


def enforce_plan_usage(user: dict[str, object]) -> None:
    usage = _build_usage_summary(user)
    if usage.jobs_limit is not None and usage.jobs_used >= usage.jobs_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the free-tier monthly limit of {usage.jobs_limit} jobs.",
        )


def get_available_plans() -> list[dict[str, object]]:
    return serialize_plans()
