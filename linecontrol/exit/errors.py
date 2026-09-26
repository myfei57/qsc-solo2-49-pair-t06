"""Exit section failures."""

from __future__ import annotations

from enum import Enum


class ExitErrorCode(str, Enum):
    RINSE_ACTIVE = "rinse-active"
    TRACK_STALE = "track-stale"


class ExitError(RuntimeError):
    def __init__(self, code: ExitErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
