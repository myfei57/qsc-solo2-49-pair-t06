"""Circulation pump controller."""

from __future__ import annotations

from collections.abc import Callable

from ..bus import EventBus
from ..pickle.tank import Tank
from ..store.filestore import FileStore
from .replenish import ReplenishOps
from .runhours import RunHourOps
from .start import StartOps
from .state import PumpData
from .status import StatusOps
from .stop import StopOps


class Pump(StartOps, StopOps, ReplenishOps, RunHourOps, StatusOps):
    """Gates circulation on a freshly evaluated tank level."""

    def __init__(
        self,
        tank: Tank,
        store: FileStore,
        bus: EventBus,
        strip_stopped: Callable[[], bool],
    ) -> None:
        self._tank = tank
        self._store = store
        self._bus = bus
        self._strip_stopped = strip_stopped
        self._state = PumpData()

    @property
    def tank(self) -> Tank:
        return self._tank

    @property
    def store(self) -> FileStore:
        return self._store

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def data(self) -> PumpData:
        return self._state

    def strip_stopped(self) -> bool:
        return self._strip_stopped()

    def snapshot(self) -> dict[str, object]:
        persisted, _ = self.persisted()
        return {
            "running": self.running(),
            "runSec": self.run_seconds(),
            "persisted": persisted.running,
            "startedAt": self.started_at().isoformat() if self.started_at() else None,
            "transitions": list(self.data.machine.history()),
        }
