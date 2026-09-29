"""Failures raised by cross-area line sequences."""

from __future__ import annotations

from enum import Enum


class LineErrorCode(str, Enum):
    PRECONDITION_LOST = "precondition-lost"
    NO_CHECKPOINT = "no-checkpoint"
    CYCLE_DONE = "cycle-done"


class LineError(RuntimeError):
    """Carries a machine-readable code in addition to the detail text."""

    def __init__(self, code: LineErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code.value, "detail": self.detail}
