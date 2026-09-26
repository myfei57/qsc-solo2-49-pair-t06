"""Durable weld tension."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import TensionSnapshot, utcnow
from ..store.keys import KEY_TENSION
from ..store.snapshot import save_json


class PersistOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def persist_tension(self, value: float, gain: float = 0.0) -> None:
        """Write the tension used for the seam before the line speeds up."""

        self.data.tension = float(value)
        snapshot = TensionSnapshot(value=float(value), gain=float(gain), saved=utcnow())
        save_json(self.store, KEY_TENSION, snapshot)
        self.bus.publish(
            Event(
                kind=EventKind.TENSION,
                source="weld",
                message="persisted",
                payload=float(value),
            )
        )

    def tension(self) -> float:
        return self.data.tension

    def restore_tension(self, snapshot: TensionSnapshot) -> None:
        self.data.tension = snapshot.value
