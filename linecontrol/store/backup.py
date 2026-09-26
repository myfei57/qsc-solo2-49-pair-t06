"""Value object describing the result of a snapshot backup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BackupSummary:
    directory: str
    files: tuple[str, ...]
    bytes_written: int

    @property
    def count(self) -> int:
        return len(self.files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "directory": self.directory,
            "files": list(self.files),
            "bytes": self.bytes_written,
            "count": self.count,
        }
