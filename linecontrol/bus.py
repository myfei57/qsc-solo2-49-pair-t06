"""In-process publish/subscribe bus used for cross-area reactions."""

from __future__ import annotations

import threading
from collections.abc import Callable

from .domain.events import Event
from .domain.kinds import EventKind

Handler = Callable[[Event], None]


class EventBus:
    """Delivers events to subscribers registered for the matching kind.

    Handlers are copied out of the registry before dispatch so that a handler
    may unsubscribe or publish a follow-up event without disturbing the
    current dispatch pass.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_id = 0
        self._subs: dict[EventKind, list[tuple[int, Handler]]] = {}
        self._delivered = 0

    def publish(self, event: Event) -> None:
        with self._lock:
            handlers = [handler for _, handler in self._subs.get(event.kind, ())]
            self._delivered += 1
        for handler in handlers:
            handler(event)

    def subscribe(self, kind: EventKind, handler: Handler) -> Callable[[], None]:
        with self._lock:
            self._next_id += 1
            token = self._next_id
            self._subs.setdefault(kind, []).append((token, handler))

        def unsubscribe() -> None:
            with self._lock:
                entries = self._subs.get(kind, [])
                self._subs[kind] = [item for item in entries if item[0] != token]

        return unsubscribe

    def subscribers(self, kind: EventKind) -> int:
        with self._lock:
            return len(self._subs.get(kind, ()))

    def delivered(self) -> int:
        with self._lock:
            return self._delivered
