"""Exit shear gated on a fresh weld track point."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .errors import ExitError, ExitErrorCode


class ShearOps:
    """Mixed into :class:`~linecontrol.exit.section.Exit`."""

    def shear(self) -> float:
        if not self.strip.shear_permit():
            raise ExitError(ExitErrorCode.TRACK_STALE, "weld track stale")
        self.data.shear_pos = self.strip.track_position() + self.data.shear_offset
        self.bus.publish(
            Event(
                kind=EventKind.SHEAR,
                source="exit",
                message="sheared",
                payload=self.data.shear_pos,
            )
        )
        return self.data.shear_pos

    def last_shear(self) -> float:
        return self.data.shear_pos

    def set_shear_offset(self, offset: float) -> None:
        self.data.shear_offset = float(offset)

    def shear_offset(self) -> float:
        return self.data.shear_offset
