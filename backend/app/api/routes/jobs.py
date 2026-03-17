from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.auth import get_optional_current_user
from app.core.database import job_repository
from app.core.jobs import job_manager
from app.core.visitor import get_visitor_id
from app.schemas.pagination import PaginatedJobs

router = APIRouter(tags=["jobs"])


@router.get("/jobs")
async def list_jobs(
    request: Request,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    viewer_user_id = str(user["id"]) if user else None
    viewer_anon_id = None if user else get_visitor_id(request)
    jobs, _ = job_manager.query_jobs(page=1, page_size=100, user_id=viewer_user_id, anon_id=viewer_anon_id)
    return jobs


@router.get("/jobs/history", response_model=PaginatedJobs)
async def paginated_jobs(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    tool: str | None = Query(default=None),
    search: str | None = Query(default=None),
    mine: bool = Query(default=False),
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    if mine and not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    viewer_user_id = str(user["id"]) if user else None
    viewer_anon_id = None if user else get_visitor_id(request)
    items, total = job_manager.query_jobs(
        page=page,
        page_size=page_size,
        status=status_filter,
        tool=tool,
        search=search,
        user_id=str(user["id"]) if mine and user else viewer_user_id,
        anon_id=None if mine else viewer_anon_id,
    )
    return PaginatedJobs(items=items, total=total, page=page, page_size=page_size)


@router.get("/jobs/{job_id}")
async def get_job(
    request: Request,
    job_id: str,
    user: dict[str, object] | None = Depends(get_optional_current_user),
):
    job = job_manager.get_job(job_id) or job_repository.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    if user:
        if job.user_id and job.user_id != str(user["id"]):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    else:
        if job.anon_id != get_visitor_id(request):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job
