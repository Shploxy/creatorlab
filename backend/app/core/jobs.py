from __future__ import annotations

import mimetypes
import queue
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import logging

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import job_repository
from app.core.exceptions import ValidationError
from app.schemas.job import JobRecord, OutputFile
from app.services.types import JobContext, OutputArtifact
from app.core.storage import storage

logger = logging.getLogger("creatorlab.jobs")

TOOL_PRIORITY_WEIGHTS = {
    "compress": 5,
    "pdf-merge": 10,
    "pdf-split": 12,
    "images-to-pdf": 18,
    "background-remove": 22,
    "upscale": 26,
}


def _download_url(file_id: str) -> str:
    return f"{settings.api_public_url.rstrip('/')}/downloads/{file_id}"


def _load_processor(tool: str):
    if tool == "upscale":
        from app.services.upscaler import process_upscale

        return process_upscale
    if tool == "background-remove":
        from app.services.background_remover import process_background_remove

        return process_background_remove
    if tool == "compress":
        from app.services.compressor import process_compress

        return process_compress
    if tool == "pdf-merge":
        from app.services.pdf_tools import process_pdf_merge

        return process_pdf_merge
    if tool == "pdf-split":
        from app.services.pdf_tools import process_pdf_split

        return process_pdf_split
    if tool == "images-to-pdf":
        from app.services.pdf_tools import process_images_to_pdf

        return process_images_to_pdf
    raise KeyError(f"Unsupported tool processor: {tool}")


class JobManager:
    def __init__(self) -> None:
        self._queue: queue.PriorityQueue[tuple[int, int, JobContext]] = queue.PriorityQueue(
            maxsize=settings.worker_queue_size
        )
        self._jobs: dict[str, JobRecord] = {}
        self._pending_entries: dict[str, tuple[int, int]] = {}
        self._threads: list[threading.Thread] = []
        self._cleanup_thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()
        self._sequence = 0
        self._cleanup_stats: dict[str, int | str] = {"deleted_files": 0, "deleted_bytes": 0, "ran_at": ""}
        self._tool_semaphores = {
            "upscale": threading.BoundedSemaphore(value=max(1, settings.max_concurrent_ai_jobs)),
            "background-remove": threading.BoundedSemaphore(value=max(1, settings.max_concurrent_ai_jobs)),
        }
        self._processors: dict[str, object] = {}

    def start(self) -> None:
        if self._running:
            return
        persisted_jobs = job_repository.load_jobs()
        with self._lock:
            self._jobs = {job.id: job for job in persisted_jobs}
            self._pending_entries = {}
        job_repository.mark_incomplete_jobs_failed()
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if job.status in {"queued", "processing"}:
                    job.status = "failed"
                    job.error = "Server restarted before the job could finish."
                    job.progress = 100
                    job.eta_seconds = 0
                    job.meta = {**job.meta, "queue_position": 0, "interrupted": True}
                    job_repository.upsert_job(job)
        self._running = True
        for index in range(settings.worker_threads):
            thread = threading.Thread(target=self._worker, name=f"creatorlab-worker-{index}", daemon=True)
            thread.start()
            self._threads.append(thread)
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, name="creatorlab-cleanup", daemon=True)
        self._cleanup_thread.start()

    def stop(self) -> None:
        self._running = False

    def create_job(
        self,
        tool: str,
        file_paths: list[Path],
        options: dict | None = None,
        user_id: str | None = None,
        anon_id: str | None = None,
        queue_owner: str | None = None,
    ) -> JobRecord:
        job_id = uuid4().hex
        now = datetime.now(timezone.utc)
        owner = queue_owner or user_id or "guest"
        meta = {
            **(options or {}),
            "attempt_count": 0,
            "max_retries": settings.job_max_retries,
            "queue_owner": owner,
        }
        record = JobRecord(
            id=job_id,
            user_id=user_id,
            anon_id=anon_id,
            tool=tool,
            status="queued",
            created_at=now,
            updated_at=now,
            input_files=[path.name for path in file_paths],
            outputs=[],
            meta=meta,
            progress=5,
            eta_seconds=20,
        )

        context = JobContext(job_id=job_id, tool=tool, file_paths=file_paths, options=options or {})
        with self._lock:
            self._jobs[job_id] = record
            priority, sequence = self._next_queue_slot_locked(record)
            record.meta = {**record.meta, "priority_score": priority}
            self._pending_entries[job_id] = (priority, sequence)
            self._refresh_pending_positions_locked()
            job_repository.upsert_job(record)
        try:
            self._queue.put_nowait((priority, sequence, context))
        except queue.Full:
            with self._lock:
                self._jobs.pop(job_id, None)
                self._pending_entries.pop(job_id, None)
                self._refresh_pending_positions_locked()
            self._cleanup_input_files(file_paths)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The processing queue is full right now. Please try again in a moment.",
            )
        return record

    def list_jobs(self) -> list[JobRecord]:
        with self._lock:
            return sorted((deepcopy(job) for job in self._jobs.values()), key=lambda item: item.created_at, reverse=True)

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job else None

    def summary(self) -> dict:
        jobs = self.list_jobs()
        queued = [job for job in jobs if job.status == "queued"]
        processing = [job for job in jobs if job.status == "processing"]
        jobs_by_tool: dict[str, int] = {}
        for job in jobs:
            jobs_by_tool[job.tool] = jobs_by_tool.get(job.tool, 0) + 1
        oldest_queued_seconds = None
        if queued:
            oldest = min(job.created_at for job in queued)
            oldest_queued_seconds = int((datetime.now(timezone.utc) - oldest).total_seconds())
        queue_groups = len({str(job.meta.get("queue_owner", "guest")) for job in queued + processing})
        return {
            "total_jobs": len(jobs),
            "failed_jobs": len([job for job in jobs if job.status == "failed"]),
            "completed_jobs": len([job for job in jobs if job.status == "completed"]),
            "queued_jobs": len(queued) + len(processing),
            "storage_usage_bytes": storage.usage_bytes(),
            "storage_breakdown": storage.usage_breakdown(),
            "processed_files": sum(len(job.outputs) for job in jobs),
            "worker_threads": settings.worker_threads,
            "queue_depth": self._queue.qsize(),
            "queue_groups": queue_groups,
            "oldest_queued_seconds": oldest_queued_seconds,
            "jobs_by_tool": jobs_by_tool,
            "cleanup": deepcopy(self._cleanup_stats),
            "recent_jobs": jobs[:10],
        }

    def _next_queue_slot_locked(self, record: JobRecord) -> tuple[int, int]:
        owner = str(record.meta.get("queue_owner", "guest"))
        owner_penalty = sum(
            1
            for job in self._jobs.values()
            if job.id != record.id
            and str(job.meta.get("queue_owner", "guest")) == owner
            and job.status in {"queued", "processing"}
        )
        tool_penalty = TOOL_PRIORITY_WEIGHTS.get(record.tool, 10)
        if record.tool == "upscale" and str(record.meta.get("quality_mode", "standard")) == "high_quality":
            tool_penalty += 24
        priority = owner_penalty * 100 + tool_penalty
        self._sequence += 1
        return priority, self._sequence

    def _worker(self) -> None:
        while self._running:
            try:
                _, _, context = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            with self._lock:
                self._pending_entries.pop(context.job_id, None)
                self._refresh_pending_positions_locked()
            self._update(
                context.job_id,
                status="processing",
                progress=35,
                eta_seconds=10,
                meta_updates={"queue_position": 0, "started_at": datetime.now(timezone.utc).isoformat()},
            )
            should_cleanup_inputs = True
            try:
                processor = self._processors.get(context.tool)
                if processor is None:
                    processor = _load_processor(context.tool)
                    self._processors[context.tool] = processor
                semaphore = self._tool_semaphores.get(context.tool)
                if semaphore:
                    with semaphore:
                        artifacts = processor(context)
                else:
                    artifacts = processor(context)
                outputs = [self._store_output(artifact) for artifact in artifacts]
                if context.tool == "pdf-split":
                    zip_output = next((output for output in outputs if output.content_type == "application/zip"), None)
                    if zip_output:
                        download_all_url = zip_output.share_url or _download_url(zip_output.file_id)
                        for output in outputs:
                            output.meta = {**output.meta, "download_all_url": download_all_url}
                current = self.get_job(context.job_id)
                next_meta = {**(current.meta if current else {}), "finished": True, "queue_position": 0}
                if context.tool == "pdf-split":
                    zip_output = next((output for output in outputs if output.content_type == "application/zip"), None)
                    pdf_count = sum(1 for output in outputs if output.content_type == "application/pdf")
                    next_meta = {
                        **next_meta,
                        "output_count": pdf_count,
                        "download_all_url": (zip_output.share_url or _download_url(zip_output.file_id)) if zip_output else None,
                    }
                self._update(
                    context.job_id,
                    status="completed",
                    progress=100,
                    eta_seconds=0,
                    outputs=outputs,
                    meta=next_meta,
                )
            except ValidationError as exc:
                logger.warning("Validation failure for job %s: %s", context.job_id, exc.detail)
                self._update(
                    context.job_id,
                    status="failed",
                    progress=100,
                    eta_seconds=0,
                    error=exc.detail,
                    meta_updates={"queue_position": 0},
                )
            except Exception as exc:  # pragma: no cover - runtime protection path
                logger.exception("Job %s failed on attempt", context.job_id)
                self._update(
                    context.job_id,
                    error=f"Processing failed: {exc}",
                    meta_updates={"last_error": str(exc), "queue_position": 0},
                )
                should_cleanup_inputs = not self._retry_job(context)
                if should_cleanup_inputs:
                    self._update(
                        context.job_id,
                        status="failed",
                        progress=100,
                        eta_seconds=0,
                        meta_updates={"queue_position": 0},
                    )
            finally:
                if should_cleanup_inputs:
                    self._cleanup_input_files(context.file_paths)
                self._queue.task_done()

    def query_jobs(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        tool: str | None = None,
        search: str | None = None,
        user_id: str | None = None,
        anon_id: str | None = None,
    ) -> tuple[list[JobRecord], int]:
        offset = max(page - 1, 0) * page_size
        return job_repository.query_jobs(
            limit=page_size,
            offset=offset,
            status=status,
            tool=tool,
            search=search,
            user_id=user_id,
            anon_id=anon_id,
        )

    def _store_output(self, artifact: OutputArtifact) -> OutputFile:
        file_id, saved_path = storage.register_output(artifact.path)
        artifact.path.unlink(missing_ok=True)
        return OutputFile(
            file_id=file_id,
            filename=artifact.filename,
            size_bytes=saved_path.stat().st_size,
            content_type=artifact.content_type or mimetypes.guess_type(saved_path.name)[0] or "application/octet-stream",
            share_url=_download_url(file_id),
            meta=artifact.meta,
        )

    def _update(self, job_id: str, **changes) -> None:
        with self._lock:
            current = self._jobs[job_id]
            meta_updates = changes.pop("meta_updates", None)
            for key, value in changes.items():
                setattr(current, key, value)
            if meta_updates:
                current.meta = {**current.meta, **meta_updates}
            current.updated_at = datetime.now(timezone.utc)
            job_repository.upsert_job(current)

    def _refresh_pending_positions_locked(self) -> None:
        ordered_ids = [
            job_id
            for job_id, _ in sorted(
                self._pending_entries.items(),
                key=lambda item: item[1],
            )
        ]
        for index, pending_id in enumerate(ordered_ids, start=1):
            current = self._jobs.get(pending_id)
            if not current:
                continue
            current.meta = {**current.meta, "queue_position": index}

    def _retry_job(self, context: JobContext) -> bool:
        current = self.get_job(context.job_id)
        if not current:
            return False
        attempt_count = int(current.meta.get("attempt_count", 0))
        max_retries = int(current.meta.get("max_retries", settings.job_max_retries))
        if attempt_count >= max_retries:
            return False

        next_attempt = attempt_count + 1
        self._update(
            context.job_id,
            status="queued",
            progress=5,
            eta_seconds=20,
            meta_updates={"attempt_count": next_attempt, "retry_scheduled": True},
        )
        with self._lock:
            queued_job = self._jobs.get(context.job_id)
            if not queued_job:
                return False
            priority, sequence = self._next_queue_slot_locked(queued_job)
            self._pending_entries[context.job_id] = (priority, sequence)
            queued_job.meta = {
                **queued_job.meta,
                "attempt_count": next_attempt,
                "retry_scheduled": True,
                "priority_score": priority,
            }
            self._refresh_pending_positions_locked()
            job_repository.upsert_job(queued_job)
        try:
            self._queue.put_nowait((priority, sequence, context))
        except queue.Full:
            return False
        return True

    def _cleanup_input_files(self, file_paths: list[Path]) -> None:
        for file_path in file_paths:
            file_path.unlink(missing_ok=True)

    def _cleanup_loop(self) -> None:
        while self._running:
            self._cleanup_stats = storage.cleanup_expired()
            job_repository.cleanup_expired_sessions()
            job_repository.cleanup_expired_auth_tokens()
            stop_event = threading.Event()
            stop_event.wait(settings.cleanup_interval_seconds)


job_manager = JobManager()
