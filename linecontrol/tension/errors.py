"""Tension roller failures."""

from __future__ import annotations

from enum import Enum


class TensionErrorCode(str, Enum):
    INVALID_GAIN = "invalid-gain"
    INVALID_SPEED = "invalid-speed"
    NOT_PERSISTED = "not-persisted"
    RAMP_UNREADY = "ramp-unready"


class TensionError(RuntimeError):
    def __init__(self, code: TensionErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
