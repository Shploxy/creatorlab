from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.auth import enforce_plan_usage, enforce_verified_email, get_optional_current_user
from app.core.config import settings
from app.core.database import job_repository
from app.core.exceptions import ValidationError
from app.core.ratelimit import enforce_upload_rate_limit
from app.core.storage import storage
from app.core.visitor import get_visitor_id, visitor_month_start
from app.core.jobs import job_manager

router = APIRouter(tags=["tools"])

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
PDF_SUFFIXES = {".pdf"}
IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
PDF_CONTENT_TYPES = {"application/pdf"}


def _save_files(
    files: list[UploadFile],
    allowed_suffixes: set[str],
    allowed_content_types: set[str],
    max_files: int,
):
    if not files:
        raise ValidationError("At least one file is required.")
    if len(files) > max_files:
        raise ValidationError(f"Too many files uploaded. Limit is {max_files}.")
    storage.ensure_directories()
    for file in files:
        if file.content_type not in allowed_content_types:
            raise ValidationError(f"Unsupported content type: {file.content_type or 'unknown'}")
    saved_paths = []
    try:
        for file in files:
            saved_paths.append(storage.save_upload(file, allowed_suffixes, settings.max_upload_mb))
    except Exception:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise
    total_size = sum(path.stat().st_size for path in saved_paths if path.exists())
    if total_size > settings.max_batch_upload_mb * 1024 * 1024:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        raise ValidationError(f"Combined upload size exceeds the {settings.max_batch_upload_mb} MB batch limit.")
    return saved_paths


def _parse_chunk_size(chunk_size: str) -> str:
    try:
        parsed_chunk_size = int(chunk_size.strip() or "2")
    except ValueError:
        parsed_chunk_size = 2
    if parsed_chunk_size <= 0:
        parsed_chunk_size = 2
    if parsed_chunk_size > settings.max_pdf_pages:
        parsed_chunk_size = settings.max_pdf_pages
    return str(parsed_chunk_size)


def _prepare_user_context(request: Request, user: dict[str, object] | None) -> tuple[str | None, str]:
    visitor_id = get_visitor_id(request)
    if settings.require_auth_for_jobs and not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to process files on this deployment.",
        )
    if user:
        if not bool(user.get("email_verified")):
            if settings.require_auth_for_jobs or settings.block_unverified_users_from_jobs:
                enforce_verified_email(user)
            return None, visitor_id
        enforce_plan_usage(user)
        return str(user["id"]), visitor_id

    anon_usage = job_repository.get_anonymous_monthly_usage(visitor_id, visitor_month_start())
    if anon_usage >= settings.anonymous_monthly_jobs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You have reached the free monthly device limit of {settings.anonymous_monthly_jobs} jobs. "
                "You can keep using your recent downloads, or create an optional account later for higher limits."
            ),
        )
    return None, visitor_id


def _queue_owner(request: Request, user_id: str | None, visitor_id: str) -> str:
    if user_id:
        return f"user:{user_id}"
    return f"anon:{visitor_id}"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "local"


@router.post("/tools/upscale/jobs")
async def create_upscale_job(
    request: Request,
    files: list[UploadFile] = File(...),
    quality_mode: str = Form(default="standard"),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AI Image Upscaler is coming soon. AI enhancement is still being refined for reliability.",
    )


@router.post("/tools/background-remove/jobs")
async def create_background_remove_job(
    request: Request,
    files: list[UploadFile] = File(...),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    paths = _save_files(files, IMAGE_SUFFIXES, IMAGE_CONTENT_TYPES, 1)
    user_id, visitor_id = _prepare_user_context(request, user)
    return job_manager.create_job(
        "background-remove",
        paths,
        {"model": settings.rembg_model_name, "client_ip": _client_ip(request)},
        user_id=user_id,
        anon_id=visitor_id if not user_id else None,
        queue_owner=_queue_owner(request, user_id, visitor_id),
    )


@router.post("/tools/compress/jobs")
async def create_compress_job(
    request: Request,
    files: list[UploadFile] = File(...),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    paths = _save_files(files, IMAGE_SUFFIXES, IMAGE_CONTENT_TYPES, 1)
    original_size = paths[0].stat().st_size if paths else 0
    user_id, visitor_id = _prepare_user_context(request, user)
    return job_manager.create_job(
        "compress",
        paths,
        {"original_size": original_size, "client_ip": _client_ip(request)},
        user_id=user_id,
        anon_id=visitor_id if not user_id else None,
        queue_owner=_queue_owner(request, user_id, visitor_id),
    )


@router.post("/tools/pdf/merge/jobs")
async def create_pdf_merge_job(
    request: Request,
    files: list[UploadFile] = File(...),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    paths = _save_files(files, PDF_SUFFIXES, PDF_CONTENT_TYPES, 10)
    user_id, visitor_id = _prepare_user_context(request, user)
    return job_manager.create_job(
        "pdf-merge",
        paths,
        {"client_ip": _client_ip(request)},
        user_id=user_id,
        anon_id=visitor_id if not user_id else None,
        queue_owner=_queue_owner(request, user_id, visitor_id),
    )


@router.post("/tools/pdf/split/jobs")
async def create_pdf_split_job(
    request: Request,
    files: list[UploadFile] = File(...),
    page_ranges: str = Form(default=""),
    mode: str = Form(default=""),
    split_mode: str = Form(default="extract_range"),
    chunk_size: str = Form(default=""),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    paths = _save_files(files, PDF_SUFFIXES, PDF_CONTENT_TYPES, 1)
    user_id, visitor_id = _prepare_user_context(request, user)
    requested_mode = (mode or split_mode).strip().lower()
    mode_aliases = {
        "range": "extract_range",
        "extract_range": "extract_range",
        "extract": "extract_range",
        "chunks": "split_chunks",
        "chunk": "split_chunks",
        "split_chunks": "split_chunks",
    }
    normalized_mode = mode_aliases.get(requested_mode)
    if not normalized_mode:
        raise ValidationError("Unsupported PDF split mode. Use range or chunks.")

    normalized_chunk_size = chunk_size.strip()
    if normalized_mode == "split_chunks":
        normalized_chunk_size = _parse_chunk_size(normalized_chunk_size)

    return job_manager.create_job(
        "pdf-split",
        paths,
        {
            "page_ranges": page_ranges,
            "mode": "chunks" if normalized_mode == "split_chunks" else "range",
            "split_mode": normalized_mode,
            "chunk_size": normalized_chunk_size,
            "client_ip": _client_ip(request),
        },
        user_id=user_id,
        anon_id=visitor_id if not user_id else None,
        queue_owner=_queue_owner(request, user_id, visitor_id),
    )


@router.post("/tools/pdf/images-to-pdf/jobs")
async def create_images_to_pdf_job(
    request: Request,
    files: list[UploadFile] = File(...),
    __: None = Depends(enforce_upload_rate_limit),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    paths = _save_files(files, IMAGE_SUFFIXES, IMAGE_CONTENT_TYPES, 20)
    user_id, visitor_id = _prepare_user_context(request, user)
    return job_manager.create_job(
        "images-to-pdf",
        paths,
        {"client_ip": _client_ip(request)},
        user_id=user_id,
        anon_id=visitor_id if not user_id else None,
        queue_owner=_queue_owner(request, user_id, visitor_id),
    )
