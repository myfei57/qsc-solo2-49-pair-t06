"""Splice release gated by the welder interlock."""

from __future__ import annotations

from collections.abc import Callable

from .errors import EntryError, EntryErrorCode


class ReleaseOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def set_interlock_provider(self, provider: Callable[[], bool] | None) -> None:
        if provider is not None:
            self._interlock = provider

    def splice_release(self) -> None:
        if self.state.alarm_seen:
            raise EntryError(EntryErrorCode.ALARM_ACTIVE, "overcurrent alarm standing")
        if not self._interlock():
            raise EntryError(EntryErrorCode.INTERLOCK_HELD, "interlock latch held")
