"""Strip tracking failures."""

from __future__ import annotations

from enum import Enum


class StripErrorCode(str, Enum):
    STRIP_RUN = "strip-run"
    TAIL_UNFLUSHED = "tail-unflushed"
    NO_SPEED = "no-speed"


class StripError(RuntimeError):
    def __init__(self, code: StripErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "detail": self.detail}
