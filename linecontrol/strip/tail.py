"""Tail rinse completion."""

from __future__ import annotations

from .errors import StripError, StripErrorCode


class TailOps:
    """Mixed into :class:`~linecontrol.strip.strip.Strip`."""

    def tail_rinse(self) -> None:
        """Clear the tail only after the strip stops and the rinse flushed."""

        if self.data.running:
            raise StripError(StripErrorCode.STRIP_RUN, "strip still running")
        if not self.flushed():
            raise StripError(StripErrorCode.TAIL_UNFLUSHED, "tail rinse not flushed")
        self.data.tail_dirty = False

    def tail_dirty(self) -> bool:
        return self.data.tail_dirty
