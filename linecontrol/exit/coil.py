"""Coil change sequence at the exit section."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind


class CoilOps:
    """Mixed into :class:`~linecontrol.exit.section.Exit`."""

    def coil_change(self) -> float:
        """Stop the rinse, lift the rolls, then shear the tail."""

        self.tank.rinse_stop()
        self.squeeze_roll_lift()
        position = self.shear()
        self.bus.publish(
            Event(
                kind=EventKind.COIL,
                source="exit",
                message="changed",
                payload=position,
            )
        )
        return position
