from pydantic import BaseModel, Field

from app.schemas.job import JobRecord


class PaginatedJobs(BaseModel):
    items: list[JobRecord] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
