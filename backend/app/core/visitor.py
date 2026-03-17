from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from app.core.config import settings


def generate_visitor_id() -> str:
    return secrets.token_urlsafe(24)


def get_visitor_id(request: Request) -> str:
    existing = request.cookies.get(settings.visitor_cookie_name)
    if existing:
        return existing
    generated = getattr(request.state, "generated_visitor_id", None)
    if generated:
        return generated
    generated = generate_visitor_id()
    request.state.generated_visitor_id = generated
    return generated


def issue_visitor_cookie(response: Response, visitor_id: str) -> None:
    secure_cookie = settings.session_cookie_secure or settings.app_env.lower() == "production"
    response.set_cookie(
        key=settings.visitor_cookie_name,
        value=visitor_id,
        httponly=True,
        secure=secure_cookie,
        samesite=settings.session_cookie_samesite,
        max_age=settings.visitor_ttl_days * 24 * 60 * 60,
        domain=settings.cookie_domain,
        path="/",
    )


def visitor_month_start() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
