"""Correlation handle generation."""

from __future__ import annotations

from uuid import uuid4


class HandleOps:
    """Mixed into :class:`~linecontrol.audit.logger.Logger`."""

    def new_handle(self) -> str:
        return uuid4().hex
