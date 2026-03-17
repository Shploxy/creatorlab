from __future__ import annotations

from abc import ABC, abstractmethod
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from app.core.config import settings
from app.core.exceptions import ValidationError

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


def sanitize_filename(filename: str | None, *, fallback: str = "upload") -> str:
    candidate = Path(filename or fallback).name
    candidate = candidate.replace("\x00", "").strip().replace("\\", "_").replace("/", "_")
    candidate = SAFE_FILENAME_PATTERN.sub("_", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip(" .")
    if not candidate:
        candidate = fallback
    if candidate in {".", ".."}:
        candidate = fallback
    return candidate[:120]


def _file_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def validate_saved_upload(path: Path, allowed_suffixes: set[str]) -> None:
    suffix = path.suffix.lower()
    if suffix not in allowed_suffixes:
        raise ValidationError(f"Unsupported file type: {suffix or 'unknown'}")

    try:
        if suffix == ".pdf":
            header = path.read_bytes()[:5]
            if header != b"%PDF-":
                raise ValidationError("Uploaded PDF files must have a valid PDF signature.")
            reader = PdfReader(str(path))
            page_count = len(reader.pages)
            if page_count <= 0:
                raise ValidationError("Uploaded PDF files must include at least one page.")
            if page_count > settings.max_pdf_pages:
                raise ValidationError(f"PDF files are limited to {settings.max_pdf_pages} pages in this version.")
            return

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
        if width <= 0 or height <= 0:
            raise ValidationError("Uploaded image files must have valid dimensions.")
        if width * height > settings.max_image_pixels:
            raise ValidationError(
                f"Uploaded image resolution is too large. Limit is {settings.max_image_pixels:,} pixels."
            )
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("The uploaded file is malformed or does not match the selected file type.")


class StorageBackend(ABC):
    @abstractmethod
    def ensure_directories(self) -> None: ...

    @abstractmethod
    def save_upload(self, upload: UploadFile, allowed_suffixes: set[str], max_size_mb: int) -> Path: ...

    @abstractmethod
    def register_output(self, source_path: Path) -> tuple[str, Path]: ...

    @abstractmethod
    def usage_bytes(self) -> int: ...

    @abstractmethod
    def usage_breakdown(self) -> dict[str, int]: ...

    @abstractmethod
    def cleanup_expired(self, output_ttl_hours: int) -> dict[str, int | str]: ...


class LocalDiskBackend(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.inputs_dir = root / "inputs"
        self.outputs_dir = root / "outputs"
        self.temp_dir = root / "temp"
        self.models_dir = root / "models"
        self.mail_dir = root / "mail"

    def ensure_directories(self) -> None:
        for directory in (self.root, self.inputs_dir, self.outputs_dir, self.temp_dir, self.models_dir, self.mail_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile, allowed_suffixes: set[str], max_size_mb: int) -> Path:
        safe_name = sanitize_filename(upload.filename)
        suffix = Path(safe_name).suffix.lower()
        if suffix not in allowed_suffixes:
            raise ValidationError(f"Unsupported file type: {suffix or 'unknown'}")

        target = self.inputs_dir / f"{uuid4().hex}{suffix}"
        size = 0
        with target.open("wb") as file_obj:
            while chunk := upload.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_size_mb * 1024 * 1024:
                    target.unlink(missing_ok=True)
                    raise ValidationError(f"File exceeds the {max_size_mb} MB limit.")
                file_obj.write(chunk)
        if size == 0:
            target.unlink(missing_ok=True)
            raise ValidationError("Uploaded files must not be empty.")
        try:
            validate_saved_upload(target, allowed_suffixes)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def register_output(self, source_path: Path) -> tuple[str, Path]:
        suffix = source_path.suffix
        file_id = f"{uuid4().hex}{suffix}"
        target = self.outputs_dir / file_id
        shutil.copy2(source_path, target)
        return file_id, target

    def usage_bytes(self) -> int:
        total = 0
        if not self.root.exists():
            return total
        for file_path in self.root.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total

    def usage_breakdown(self) -> dict[str, int]:
        self.ensure_directories()
        return {
            "inputs_bytes": sum(_file_bytes(path) for path in self.inputs_dir.rglob("*") if path.is_file()),
            "outputs_bytes": sum(_file_bytes(path) for path in self.outputs_dir.rglob("*") if path.is_file()),
            "temp_bytes": sum(_file_bytes(path) for path in self.temp_dir.rglob("*") if path.is_file()),
            "models_bytes": sum(_file_bytes(path) for path in self.models_dir.rglob("*") if path.is_file()),
            "mail_bytes": sum(_file_bytes(path) for path in self.mail_dir.rglob("*") if path.is_file()),
        }

    def cleanup_expired(self, output_ttl_hours: int) -> dict[str, int | str]:
        deleted_files = 0
        deleted_bytes = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.temp_file_ttl_hours)
        for directory in (self.inputs_dir, self.temp_dir):
            if not directory.exists():
                continue
            for file_path in directory.rglob("*"):
                if not file_path.is_file():
                    continue
                modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if modified < cutoff:
                    deleted_bytes += file_path.stat().st_size
                    deleted_files += 1
                    file_path.unlink(missing_ok=True)

        output_cutoff = datetime.now(timezone.utc) - timedelta(hours=output_ttl_hours)
        if self.outputs_dir.exists():
            for file_path in self.outputs_dir.iterdir():
                if not file_path.is_file():
                    continue
                modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                if modified < output_cutoff:
                    deleted_bytes += file_path.stat().st_size
                    deleted_files += 1
                    file_path.unlink(missing_ok=True)

        return {
            "deleted_files": deleted_files,
            "deleted_bytes": deleted_bytes,
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }


class StorageManager:
    def __init__(self, backend: StorageBackend) -> None:
        self.backend = backend
        self.root = settings.storage_root
        self.inputs_dir = self.root / "inputs"
        self.outputs_dir = self.root / "outputs"
        self.temp_dir = self.root / "temp"
        self.models_dir = self.root / "models"

    def ensure_directories(self) -> None:
        self.backend.ensure_directories()

    def save_upload(self, upload: UploadFile, allowed_suffixes: set[str], max_size_mb: int) -> Path:
        return self.backend.save_upload(upload, allowed_suffixes, max_size_mb)

    def register_output(self, source_path: Path) -> tuple[str, Path]:
        return self.backend.register_output(source_path)

    def usage_bytes(self) -> int:
        return self.backend.usage_bytes()

    def usage_breakdown(self) -> dict[str, int]:
        return self.backend.usage_breakdown()

    def cleanup_expired(self) -> dict[str, int | str]:
        return self.backend.cleanup_expired(settings.output_file_ttl_hours)


storage = StorageManager(LocalDiskBackend(settings.storage_root))
