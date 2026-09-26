"""Atomic file store rooted at a single directory."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Sequence
from pathlib import Path

from .backup import BackupSummary


class FileStore:
    """Key/value files written through a temporary file plus rename.

    Writes are serialised by a lock so that a snapshot is either the previous
    complete payload or the new complete payload, never a partial file.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @property
    def directory(self) -> str:
        return str(self._dir)

    def _path(self, key: str) -> Path:
        if not key or "/" in key or "\\" in key or key in {".", ".."}:
            raise ValueError(f"invalid snapshot key: {key!r}")
        return self._dir / key

    def save(self, key: str, payload: bytes) -> None:
        path = self._path(key)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with self._lock:
            tmp.write_bytes(payload)
            os.replace(tmp, path)

    def load(self, key: str) -> bytes | None:
        path = self._path(key)
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return None

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list(self, prefix: str = "") -> list[str]:
        with self._lock:
            names = sorted(entry.name for entry in self._dir.iterdir() if entry.is_file())
        if not prefix:
            return names
        return [name for name in names if name.startswith(prefix)]

    def rotate(self, key: str, keep: int) -> int:
        """Trim a JSON array snapshot to its newest ``keep`` entries."""

        raw = self.load(key)
        if raw is None or keep <= 0:
            return 0
        try:
            items = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return 0
        if not isinstance(items, list) or len(items) <= keep:
            return 0
        dropped = len(items) - keep
        self.save(key, json.dumps(items[dropped:], ensure_ascii=False).encode("utf-8"))
        return dropped

    def backup(self) -> BackupSummary:
        """Copy every current snapshot into a ``backup`` subdirectory."""

        with self._lock:
            target = self._dir / "backup"
            target.mkdir(parents=True, exist_ok=True)
            copied: list[str] = []
            total = 0
            for entry in sorted(self._dir.iterdir()):
                if not entry.is_file():
                    continue
                data = entry.read_bytes()
                (target / entry.name).write_bytes(data)
                copied.append(entry.name)
                total += len(data)
        return BackupSummary(
            directory=str(target),
            files=tuple(copied),
            bytes_written=total,
        )

    def backup_files(self) -> Sequence[str]:
        target = self._dir / "backup"
        if not target.is_dir():
            return ()
        return tuple(sorted(entry.name for entry in target.iterdir() if entry.is_file()))
