"""Audit logger state."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.events import Event

#: Number of events kept in memory and on disk.
MAX_EVENTS = 500

#: Default number of events returned by a query without an explicit limit.
DEFAULT_QUERY_LIMIT = 50


@dataclass(slots=True)
class AuditState:
    events: list[Event] = field(default_factory=list)
    alarms: dict[str, bool] = field(default_factory=dict)

    def trim(self, keep: int = MAX_EVENTS) -> int:
        """Drop the oldest events beyond ``keep`` and report how many went."""

        if len(self.events) <= keep:
            return 0
        dropped = len(self.events) - keep
        del self.events[:dropped]
        return dropped
