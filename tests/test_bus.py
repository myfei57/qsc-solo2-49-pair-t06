"""Process event bus behaviour."""

from __future__ import annotations

from linecontrol.bus import EventBus
from linecontrol.domain.events import Event
from linecontrol.domain.kinds import EventKind


def test_publish_only_reaches_matching_kind() -> None:
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe(EventKind.ARC, lambda event: seen.append(event.message))
    bus.publish(Event(kind=EventKind.ARC, source="weld", message="struck"))
    bus.publish(Event(kind=EventKind.STOP, source="line", message="stopped"))
    assert seen == ["struck"]
    assert bus.delivered() == 2
    assert bus.subscribers(EventKind.ARC) == 1


def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    seen: list[str] = []
    stop = bus.subscribe(EventKind.TRACK, lambda event: seen.append(event.message))
    bus.publish(Event(kind=EventKind.TRACK, source="strip", message="first"))
    stop()
    bus.publish(Event(kind=EventKind.TRACK, source="strip", message="second"))
    assert seen == ["first"]
    assert bus.subscribers(EventKind.TRACK) == 0


def test_handler_may_publish_a_follow_up_event() -> None:
    bus = EventBus()
    seen: list[EventKind] = []

    def follow(event: Event) -> None:
        seen.append(event.kind)
        if event.kind is EventKind.ARC:
            bus.publish(Event(kind=EventKind.WELD, source="weld", message="seam"))

    bus.subscribe(EventKind.ARC, follow)
    bus.subscribe(EventKind.WELD, follow)
    bus.publish(Event(kind=EventKind.ARC, source="weld", message="struck"))
    assert seen == [EventKind.ARC, EventKind.WELD]
