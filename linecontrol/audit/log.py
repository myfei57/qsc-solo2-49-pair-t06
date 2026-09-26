"""Append-only event log with a bounded on-disk window."""

from __future__ import annotations

from ..domain.events import Event
from ..store.keys import KEY_EVENTS
from ..store.snapshot import load_events, save_events
from .state import MAX_EVENTS


class LogOps:
    """Mixed into :class:`~linecontrol.audit.logger.Logger`."""

    def record(self, event: Event) -> int:
        """Append an event; returns the number of trimmed entries."""

        self.state.events.append(event)
        dropped = self.state.trim(MAX_EVENTS)
        self._flush()
        return dropped

    def events(self) -> tuple[Event, ...]:
        return tuple(self.state.events)

    def restore(self) -> int:
        """Reload the log from disk; returns the number of events restored."""

        raw = load_events(self.store, KEY_EVENTS)
        restored = [Event.from_dict(item) for item in raw]
        self.state.events = restored
        self.state.trim(MAX_EVENTS)
        return len(self.state.events)

    def flush(self) -> int:
        return self._flush()

    def _flush(self) -> int:
        payload = [event.to_dict() for event in self.state.events]
        save_events(self.store, KEY_EVENTS, payload)
        return self.store.rotate(KEY_EVENTS, MAX_EVENTS)
