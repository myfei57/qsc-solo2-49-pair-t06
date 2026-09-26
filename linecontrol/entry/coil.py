"""Coil load and coil change handling."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .errors import EntryError, EntryErrorCode


class CoilOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def load_coil(self, coil_id: str, target: float) -> None:
        if not coil_id:
            raise EntryError(EntryErrorCode.NO_COIL, "no coil loaded")
        self.state.reset_for_coil(coil_id, float(target))
        self.bus.publish(
            Event(
                kind=EventKind.COIL,
                source="entry",
                message=coil_id,
                payload=float(target),
            )
        )

    def coil_change(self) -> None:
        if not self.state.coil_id:
            raise EntryError(EntryErrorCode.NO_COIL, "no coil loaded")
        self.state.clear_coil()
        self.bus.publish(Event(kind=EventKind.COIL, source="entry", message="coil changed"))

    def coil_id(self) -> str:
        return self.state.coil_id
