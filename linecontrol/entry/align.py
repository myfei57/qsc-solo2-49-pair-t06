"""Head alignment confirmation."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import Confirm, utcnow
from .errors import EntryError, EntryErrorCode


class AlignOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def align_confirm(self) -> None:
        state = self.state
        if not state.coil_id:
            raise EntryError(EntryErrorCode.NO_COIL, "no coil loaded")
        state.confirm = Confirm(ok=True, position=state.target, at=utcnow())
        self.bus.publish(
            Event(
                kind=EventKind.ALIGN,
                source="entry",
                message="aligned",
                payload=state.target,
            )
        )

    def align_refresh(self, position: float) -> None:
        """Publish a fresher alignment position for the next gate read.

        The refresh is written straight onto the shared confirmation so that a
        gate reading the confirmation after this call observes the new
        position rather than the value captured at the previous confirm.
        """

        state = self.state
        state.confirm = Confirm(ok=True, position=float(position), at=utcnow())
        self.bus.publish(
            Event(
                kind=EventKind.ALIGN,
                source="entry",
                message="refreshed",
                payload=float(position),
            )
        )

    def confirm_state(self) -> Confirm:
        return self.confirm()
