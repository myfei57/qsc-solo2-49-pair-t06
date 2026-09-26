"""Entry section failures."""

from __future__ import annotations

from enum import Enum


class EntryErrorCode(str, Enum):
    NO_COIL = "no-coil"
    INTERLOCK_HELD = "interlock-held"
    ALARM_ACTIVE = "alarm-active"


class EntryError(RuntimeError):
    def __init__(self, code: EntryErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
