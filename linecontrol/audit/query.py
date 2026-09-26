"""Event queries."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .state import DEFAULT_QUERY_LIMIT


class QueryOps:
    """Mixed into :class:`~linecontrol.audit.logger.Logger`."""

    def query(self, kind: EventKind, limit: int = 0) -> list[Event]:
        """Newest-first events of one kind."""

        cap = limit if limit > 0 else DEFAULT_QUERY_LIMIT
        found: list[Event] = []
        for event in reversed(self.state.events):
            if event.kind is kind:
                found.append(event)
                if len(found) >= cap:
                    break
        return found

    def recent(self, limit: int) -> list[Event]:
        if limit <= 0:
            return []
        return self.state.events[-limit:]
