"""Audit logger assembling the audit mixins."""

from __future__ import annotations

from ..bus import EventBus
from ..store.filestore import FileStore
from .alarm import AlarmOps
from .handle import HandleOps
from .log import LogOps
from .query import QueryOps
from .state import AuditState
from .summary import SummaryOps


class Logger(LogOps, AlarmOps, QueryOps, SummaryOps, HandleOps):
    """Stores every process event and the current alarm register."""

    def __init__(self, store: FileStore, bus: EventBus) -> None:
        self._store = store
        self._bus = bus
        self._state = AuditState()

    @property
    def store(self) -> FileStore:
        return self._store

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def state(self) -> AuditState:
        return self._state

    def snapshot(self) -> dict[str, object]:
        return {
            "events": [event.to_dict() for event in self.recent(20)],
            "alarms": self.active_alarms(),
            "summary": self.summary(),
        }
