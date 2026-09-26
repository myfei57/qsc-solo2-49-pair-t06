"""Dryer controller."""

from __future__ import annotations

from collections.abc import Callable

from ..bus import EventBus
from .heat import HeatOps
from .profile import ProfileOps
from .reheat import ReheatOps
from .session import SessionOps
from .state import DryerData


class Dryer(HeatOps, ProfileOps, ReheatOps, SessionOps):
    """Refuses to heat until exhaust has been established.

    The exhaust lookup is a callable owned by the exit section, so both the
    first heat and the recovery re-heat read the live exhaust state.
    """

    def __init__(self, exhaust_ok: Callable[[], bool], bus: EventBus) -> None:
        self._exhaust_ok = exhaust_ok
        self._bus = bus
        self._state = DryerData()

    @property
    def data(self) -> DryerData:
        return self._state

    @property
    def bus(self) -> EventBus:
        return self._bus

    def exhaust_ok(self) -> bool:
        return bool(self._exhaust_ok())

    def temp(self) -> float:
        return self.data.temp

    def snapshot(self) -> dict[str, object]:
        return {
            "heating": self.data.heating(),
            "temp": self.temp(),
            "dew": self.dew_point(),
            "cycles": self.heat_cycles(),
            "session": self.session_seconds(),
            "state": self.data.machine.state,
            "transitions": list(self.data.machine.history()),
        }
