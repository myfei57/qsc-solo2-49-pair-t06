"""Pickling tank failures."""

from __future__ import annotations

from enum import Enum


class PickleErrorCode(str, Enum):
    TANK_VOLUME = "tank-volume"
    OFFSET_INVALID = "offset-invalid"


class PickleError(RuntimeError):
    def __init__(self, code: PickleErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
