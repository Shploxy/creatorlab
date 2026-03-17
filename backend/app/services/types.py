from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class JobContext:
    job_id: str
    tool: str
    file_paths: list[Path]
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputArtifact:
    path: Path
    content_type: str
    filename: str
    meta: dict[str, Any] = field(default_factory=dict)
