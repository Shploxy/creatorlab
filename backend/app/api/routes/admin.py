from __future__ import annotations

import platform
import threading

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_optional_current_user
from app.core.config import settings
from app.core.database import job_repository
from app.core.jobs import job_manager
from app.core.mail import mail_provider
from app.core.runtime import get_runtime_info

router = APIRouter(tags=["admin"])


@router.get("/admin/summary")
async def admin_summary(user: dict[str, object] | None = Depends(get_optional_current_user)):
    if settings.app_env.lower() == "production" and not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    summary = job_manager.summary()
    summary["runtime"] = get_runtime_info()
    summary["auth"] = {
        "active_sessions": job_repository.count_active_sessions(),
        "pending_tokens": job_repository.count_pending_auth_tokens(),
    }
    summary["mail"] = mail_provider.stats()
    summary["system"] = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "active_threads": threading.active_count(),
    }
    return summary
