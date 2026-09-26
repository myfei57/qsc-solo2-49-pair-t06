"""Exhaust establishment.

The dryer reads this flag through a callable, so the flag must be published on
the bus as well as stored locally for the console.
"""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind


class ExhaustOps:
    """Mixed into :class:`~linecontrol.exit.section.Exit`."""

    def exhaust_establish(self) -> None:
        self.data.exhaust = True
        self.bus.publish(
            Event(kind=EventKind.EXHAUST, source="exit", message="established")
        )

    def exhaust_ok(self) -> bool:
        return self.data.exhaust

    def exhaust_reset(self) -> None:
        self.data.exhaust = False
        self.bus.publish(Event(kind=EventKind.EXHAUST, source="exit", message="lost"))
