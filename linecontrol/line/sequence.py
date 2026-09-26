"""Ordered record of the steps taken by one line sequence."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime

from ..domain.records import utcnow


@dataclass(frozen=True, slots=True)
class StepRecord:
    """One step of a sequence, with the failure text when it did not pass."""

    name: str
    ok: bool
    detail: str
    at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ok": self.ok,
            "detail": self.detail,
            "at": self.at.isoformat(),
        }


class Sequence:
    """Collects the steps and failures of a multi-stage line action."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._label = ""
        self._started: datetime | None = None
        self._steps: list[StepRecord] = []

    def begin(self, label: str) -> None:
        with self._lock:
            self._label = label
            self._started = utcnow()
            self._steps.clear()

    def begin_if_idle(self, label: str) -> None:
        """Start a label only when no sequence is already running."""

        with self._lock:
            if self._label:
                return
            self._label = label
            self._started = utcnow()
            self._steps.clear()

    def label(self) -> str:
        with self._lock:
            return self._label

    def record(self, name: str, error: Exception | None = None) -> StepRecord:
        with self._lock:
            step = StepRecord(
                name=name,
                ok=error is None,
                detail="" if error is None else str(error),
                at=utcnow(),
            )
            self._steps.append(step)
            return step

    def failures(self) -> tuple[StepRecord, ...]:
        with self._lock:
            return tuple(step for step in self._steps if not step.ok)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "label": self._label,
                "started": self._started.isoformat() if self._started else None,
                "steps": [step.to_dict() for step in self._steps],
            }

    def clear(self) -> None:
        with self._lock:
            self._steps.clear()
            self._label = ""
            self._started = None
