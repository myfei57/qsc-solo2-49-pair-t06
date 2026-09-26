"""Dryer failures."""

from __future__ import annotations

from enum import Enum


class DryerErrorCode(str, Enum):
    NO_EXHAUST = "no-exhaust"
    DEW_HIGH = "dew-high"
    TEMP_RANGE = "temp-range"


class DryerError(RuntimeError):
    def __init__(self, code: DryerErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
