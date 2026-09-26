"""Exhaust-gated heating."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .errors import DryerError, DryerErrorCode
from .state import HEAT_START_TEMP


class HeatOps:
    """Mixed into :class:`~linecontrol.dry.dryer.Dryer`."""

    def heat_gate(self) -> None:
        """Refuse to raise the chamber temperature without exhaust."""

        if not self.exhaust_ok():
            raise DryerError(DryerErrorCode.NO_EXHAUST, "exhaust not established")

    def heat(self) -> None:
        self.heat_gate()
        self.begin_heat()
        self.data.temp = HEAT_START_TEMP
        self.announce("heating")

    def announce(self, message: str) -> None:
        """Publish the current chamber temperature for this heat step."""

        self.bus.publish(
            Event(
                kind=EventKind.DRY,
                source="dry",
                message=message,
                payload=self.data.temp,
            )
        )
