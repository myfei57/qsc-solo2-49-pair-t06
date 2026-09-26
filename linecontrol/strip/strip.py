"""Strip tracking controller."""

from __future__ import annotations

from collections.abc import Callable

from ..bus import EventBus
from ..store.filestore import FileStore
from .sag import SagOps
from .speed import SpeedOps
from .state import StripState
from .stop import StopOps
from .tail import TailOps
from .track import TrackOps


class Strip(TrackOps, SpeedOps, StopOps, TailOps, SagOps):
    """Follows the seam position down the line.

    The gain and rinse lookups are callables owned by other sections so the
    strip package never reaches into their private state.
    """

    def __init__(
        self,
        store: FileStore,
        bus: EventBus,
        gain: Callable[[], float],
        flushed: Callable[[], bool],
    ) -> None:
        self._store = store
        self._bus = bus
        self._gain = gain
        self._flushed = flushed
        self._state = StripState()

    @property
    def store(self) -> FileStore:
        return self._store

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def data(self) -> StripState:
        return self._state

    def gain(self) -> float:
        return float(self._gain())

    def flushed(self) -> bool:
        return bool(self._flushed())

    def snapshot(self) -> dict[str, object]:
        return {
            "running": self.running(),
            "track": self.track_position(),
            "seam": self.seam_id(),
            "tailDirty": self.tail_dirty(),
            "speed": self.speed(),
            "travel": self.travel(),
            "sag": self.sag_check(),
        }
