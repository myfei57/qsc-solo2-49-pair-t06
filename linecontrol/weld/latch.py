"""Overcurrent alarm and the interlock latch it leaves behind."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import LatchSnapshot, utcnow
from ..store.keys import KEY_LATCH
from ..store.snapshot import save_json


class LatchOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def alarm(self) -> None:
        self.data.alarm = True
        self.data.latch = True
        self._save_latch()
        self.bus.publish(
            Event(kind=EventKind.ALARM, source="weld", message="overcurrent")
        )

    def alarm_clear(self) -> None:
        self.data.alarm = False
        self.data.latch = False
        self._save_latch()
        self.bus.publish(
            Event(kind=EventKind.LATCH, source="weld", message="interlock released")
        )

    def interlock_ok(self) -> bool:
        return not self.data.latch

    def alarm_active(self) -> bool:
        return self.data.alarm

    def restore_latch(self, snapshot: LatchSnapshot) -> None:
        self.data.latch = snapshot.interlock
        self.data.alarm = snapshot.alarm

    def _save_latch(self) -> None:
        save_json(
            self.store,
            KEY_LATCH,
            LatchSnapshot(
                interlock=self.data.latch,
                alarm=self.data.alarm,
                saved=utcnow(),
            ),
        )
