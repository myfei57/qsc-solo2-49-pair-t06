"""Exit section controller."""

from __future__ import annotations

from ..bus import EventBus
from ..pickle.tank import Tank
from ..strip.strip import Strip
from .coil import CoilOps
from .exhaust import ExhaustOps
from .roll import RollOps
from .shear import ShearOps
from .state import ExitState
from .taper import TaperOps


class Exit(ExhaustOps, RollOps, ShearOps, TaperOps, CoilOps):
    """Owns the exhaust state, the squeeze rolls and the exit shear."""

    def __init__(self, tank: Tank, strip: Strip, bus: EventBus) -> None:
        self._tank = tank
        self._strip = strip
        self._bus = bus
        self._state = ExitState()

    @property
    def tank(self) -> Tank:
        return self._tank

    @property
    def strip(self) -> Strip:
        return self._strip

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def data(self) -> ExitState:
        return self._state

    def snapshot(self) -> dict[str, object]:
        return {
            "exhaust": self.exhaust_ok(),
            "rollUp": self.roll_up(),
            "shear": self.last_shear(),
            "taper": self.taper(),
            "shearOffset": self.shear_offset(),
        }
