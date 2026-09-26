"""Rinse valve, flush flag and its snapshot."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import RinseSnapshot, utcnow
from ..store.keys import KEY_RINSE
from ..store.snapshot import load_json, save_json


class RinseOps:
    """Mixed into :class:`~linecontrol.pickle.tank.Tank`."""

    def rinse(self) -> None:
        self.data.valve_open = True
        self.data.flushed = False
        self._save_rinse()
        self.bus.publish(Event(kind=EventKind.RINSE, source="pickle", message="rinsing"))

    def rinse_flush(self) -> None:
        self.data.flushed = True
        self.bus.publish(Event(kind=EventKind.RINSE, source="pickle", message="flushed"))

    def rinse_stop(self) -> None:
        self.data.valve_open = False
        self._save_rinse()
        self.bus.publish(Event(kind=EventKind.RINSE, source="pickle", message="stopped"))

    def rinsing(self) -> bool:
        return self.data.valve_open

    def flushed(self) -> bool:
        return self.data.flushed

    def restore_rinse(self, active: bool) -> None:
        self.data.valve_open = active

    def rinse_persisted(self) -> tuple[RinseSnapshot, bool]:
        return load_json(self.store, KEY_RINSE, RinseSnapshot)

    def _save_rinse(self) -> None:
        save_json(
            self.store,
            KEY_RINSE,
            RinseSnapshot(active=self.data.valve_open, saved=utcnow()),
        )
