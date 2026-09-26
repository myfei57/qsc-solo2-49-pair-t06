"""Pickling tank controller."""

from __future__ import annotations

from ..bus import EventBus
from ..store.filestore import FileStore
from .concentration import ConcentrationOps
from .dosing import DosingOps
from .level import LevelOps
from .rinse import RinseOps
from .state import TankState
from .trend import TrendOps


class Tank(LevelOps, ConcentrationOps, DosingOps, RinseOps, TrendOps):
    """Owns the acid level, the calibration offset and the rinse valve."""

    def __init__(self, store: FileStore, bus: EventBus) -> None:
        self._store = store
        self._bus = bus
        self._state = TankState()

    @property
    def store(self) -> FileStore:
        return self._store

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def data(self) -> TankState:
        return self._state

    def snapshot(self) -> dict[str, object]:
        persisted, _ = self.rinse_persisted()
        return {
            "level": self.level(),
            "rinsing": self.rinsing(),
            "offset": self.offset(),
            "flushed": self.flushed(),
            "trend": self.level_trend(),
            "rinsingPersist": persisted.active,
        }
