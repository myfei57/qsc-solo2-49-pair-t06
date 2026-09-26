"""Circulation pump failures."""

from __future__ import annotations

from enum import Enum


class PumpErrorCode(str, Enum):
    LEVEL_LOW = "level-low"
    STRIP_RUN = "strip-run"
    NO_REPLENISH = "no-replenish"


class PumpError(RuntimeError):
    def __init__(self, code: PumpErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
