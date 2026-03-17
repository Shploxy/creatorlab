from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OutputFile(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    content_type: str
    share_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class JobRecord(BaseModel):
    id: str
    user_id: str | None = None
    anon_id: str | None = None
    tool: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    input_files: list[str] = Field(default_factory=list)
    outputs: list[OutputFile] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    progress: int = 0
    eta_seconds: int | None = None


class AdminSummary(BaseModel):
    total_jobs: int
    failed_jobs: int
    completed_jobs: int
    queued_jobs: int
    storage_usage_bytes: int
    storage_breakdown: dict[str, int] = Field(default_factory=dict)
    processed_files: int
    worker_threads: int | None = None
    queue_depth: int | None = None
    queue_groups: int | None = None
    oldest_queued_seconds: int | None = None
    jobs_by_tool: dict[str, int] = Field(default_factory=dict)
    cleanup: dict[str, Any] = Field(default_factory=dict)
    auth: dict[str, Any] = Field(default_factory=dict)
    mail: dict[str, Any] = Field(default_factory=dict)
    system: dict[str, Any] = Field(default_factory=dict)
    recent_jobs: list[JobRecord]
