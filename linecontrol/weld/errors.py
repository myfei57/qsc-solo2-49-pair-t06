"""Welder failures."""

from __future__ import annotations

from enum import Enum


class WeldErrorCode(str, Enum):
    ALIGN_PENDING = "align-pending"
    ARC_BLOCKED = "arc-blocked"
    LATCH_HELD = "latch-held"
    POWER_INVALID = "power-invalid"


class WeldError(RuntimeError):
    def __init__(self, code: WeldErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
