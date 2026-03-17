from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_optional_current_user, serialize_user_session
from app.core.config import settings
from app.core.database import job_repository
from app.core.plans import get_plan
from app.core.visitor import get_visitor_id, visitor_month_start

router = APIRouter(tags=["visitor"])


@router.get("/visitor/status")
async def visitor_status(
    request: Request,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    if user:
        return {
            "mode": "account",
            "authenticated": True,
            "user": serialize_user_session(user),
        }

    visitor_id = get_visitor_id(request)
    used = job_repository.get_anonymous_monthly_usage(visitor_id, visitor_month_start())
    remaining = max(settings.anonymous_monthly_jobs - used, 0)
    creator_plan = get_plan("creator")
    return {
        "mode": "anonymous",
        "authenticated": False,
        "visitor_id": visitor_id,
        "usage": {
            "jobs_used": used,
            "jobs_limit": settings.anonymous_monthly_jobs,
            "jobs_remaining": remaining,
        },
        "upgrade": {
            "title": "Optional account upgrade",
            "description": "Create an account later for higher limits, cross-device history, and faster paid tiers.",
            "starting_price_usd": creator_plan.monthly_price_usd,
        },
    }
