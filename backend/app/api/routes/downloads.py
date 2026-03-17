from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.core.auth import get_optional_current_user
from app.core.database import job_repository
from app.core.storage import sanitize_filename, storage
from app.core.visitor import get_visitor_id

router = APIRouter(tags=["downloads"])


def _authorize_download(request: Request, file_id: str, user: dict[str, object] | None) -> tuple[Path, str, str]:
    job = job_repository.get_job_by_output_file_id(file_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    if user:
        if job.user_id and job.user_id != str(user["id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    else:
        visitor_id = get_visitor_id(request)
        if job.anon_id != visitor_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    output = next((item for item in job.outputs if item.file_id == file_id), None)
    if not output:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    file_path = storage.outputs_dir / file_id
    try:
        resolved_path = file_path.resolve(strict=True)
        outputs_dir = storage.outputs_dir.resolve(strict=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.") from exc

    if outputs_dir not in resolved_path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    return resolved_path, sanitize_filename(output.filename, fallback=file_id), output.content_type


@router.get("/downloads/{file_id}")
async def download_output(
    file_id: str,
    request: Request,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    file_path, filename, content_type = _authorize_download(request, file_id, user)
    response = FileResponse(file_path, media_type=content_type, filename=filename)
    response.headers["Cache-Control"] = "private, max-age=3600"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"
    return response
