"""Seam generation and its persisted record."""

from __future__ import annotations

from uuid import uuid4

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import WeldRecord, utcnow
from ..store.keys import KEY_WELD, SEAM_PREFIX
from ..store.snapshot import save_json
from .errors import WeldError, WeldErrorCode
from .state import WeldState


class SpliceOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def splice(self) -> WeldRecord:
        if self.state() != WeldState.WELDING:
            raise WeldError(WeldErrorCode.ARC_BLOCKED, "no arc running")
        record = WeldRecord(
            seam_id=uuid4().hex,
            position=self.data.track,
            tension=self.data.tension,
            heat_input=self.heat_input(),
            at=utcnow(),
        )
        save_json(self.store, KEY_WELD, record)
        save_json(self.store, SEAM_PREFIX + record.seam_id, record)
        self.data.seam_id = record.seam_id
        self.machine.enter(WeldState.SPLICED)
        self.bus.publish(
            Event(
                kind=EventKind.WELD,
                source="weld",
                message=record.seam_id,
                payload=record.position,
            )
        )
        return record

    def track_point(self) -> float:
        return self.data.track

    def seam_id(self) -> str:
        return self.data.seam_id
