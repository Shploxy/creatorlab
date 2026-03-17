from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, auth, billing, downloads, jobs, tools, visitor
from app.core.config import settings
from app.core.database import job_repository
from app.core.jobs import job_manager
from app.core.logging_config import setup_logging
from app.core.mail import mail_provider
from app.core.runtime import get_runtime_info
from app.core.storage import storage
from app.core.visitor import get_visitor_id, issue_visitor_cookie

setup_logging()
storage.ensure_directories()
mail_provider.ensure_directories()
logger = logging.getLogger("creatorlab.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env.lower() == "production":
        if not settings.session_cookie_secure:
            raise RuntimeError("SESSION_COOKIE_SECURE must be enabled in production.")
        if settings.auth_secret_key and len(settings.auth_secret_key) < 32:
            raise RuntimeError("AUTH_SECRET_KEY must be set to a strong production value.")
    job_repository.initialize()
    job_manager.start()
    logger.info(
        "CreatorLab API started | env=%s | storage=%s | require_auth_for_jobs=%s | require_email_verification=%s | mail_backend=%s | runtime=%s",
        settings.app_env,
        settings.storage_backend,
        settings.require_auth_for_jobs,
        settings.require_email_verification,
        settings.mail_backend,
        get_runtime_info(),
    )
    yield
    job_manager.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(visitor.router, prefix="/api")
app.include_router(downloads.router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", uuid4().hex)
    started_at = time.perf_counter()
    visitor_id = get_visitor_id(request)
    content_length = request.headers.get("content-length")
    if request.url.path.startswith("/api/tools/") and content_length:
        try:
            if int(content_length) > settings.max_request_mb * 1024 * 1024:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body exceeds the {settings.max_request_mb} MB request limit.",
                        "request_id": request_id,
                    },
                )
        except ValueError:
            pass
    try:
        response = await call_next(request)
    except Exception:  # pragma: no cover - defensive logging path
        logger.exception("Unhandled error for %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Unexpected server error.", "request_id": request_id},
        )

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    if request.cookies.get(settings.visitor_cookie_name) != visitor_id:
        issue_visitor_cookie(response, visitor_id)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(duration_ms)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    log_method = logger.warning if response.status_code >= 400 else logger.info
    log_method("%s %s -> %s in %sms", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/ready")
async def ready():
    return {
        "status": "ready",
        "storage_backend": settings.storage_backend,
        "runtime": {"device": get_runtime_info().get("device"), "cuda_available": get_runtime_info().get("cuda_available")},
    }
