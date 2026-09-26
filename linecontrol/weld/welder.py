"""Welder controller assembling the weld-cycle mixins."""

from __future__ import annotations

from collections.abc import Callable

from ..bus import EventBus
from ..domain.machine import StateMachine
from ..domain.records import Confirm
from ..store.filestore import FileStore
from .arc import ArcOps
from .gate import GateOps
from .latch import LatchOps
from .persist import PersistOps
from .power import PowerOps
from .seams import SeamsOps
from .splice import SpliceOps
from .state import WeldStateData, new_weld_machine


class Welder(GateOps, ArcOps, SpliceOps, LatchOps, PowerOps, PersistOps, SeamsOps):
    """Gates the arc on the current alignment confirmation.

    The alignment lookup is a callable rather than a stored copy so that a
    confirmation refreshed by the entry section is observed by the next gate
    read on both the start-up and the post-splice arc path.
    """

    def __init__(
        self,
        align: Callable[[], Confirm],
        store: FileStore,
        bus: EventBus,
    ) -> None:
        self._align = align
        self._store = store
        self._bus = bus
        self._state = WeldStateData()
        self._machine: StateMachine = new_weld_machine()

    @property
    def store(self) -> FileStore:
        return self._store

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def data(self) -> WeldStateData:
        return self._state

    @property
    def machine(self) -> StateMachine:
        return self._machine

    def state(self) -> str:
        return self._machine.state

    def snapshot(self) -> dict[str, object]:
        voltage, current = self.power_state()
        return {
            "state": self.state(),
            "track": self.track_point(),
            "seam": self.seam_id(),
            "alarm": self.alarm_active(),
            "interlock": self.interlock_ok(),
            "tension": self.tension(),
            "heatInput": self.heat_input(),
            "voltage": voltage,
            "current": current,
            "transitions": list(self._machine.history()),
        }
