"""Audit log, alarm register and queries."""

from __future__ import annotations

from linecontrol.audit.logger import Logger
from linecontrol.audit.state import MAX_EVENTS
from linecontrol.bus import EventBus
from linecontrol.domain.events import Event
from linecontrol.domain.kinds import EventKind
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import KEY_EVENTS


def build(tmp_path) -> Logger:
    return Logger(FileStore(tmp_path), EventBus())


def test_record_trims_and_persists(tmp_path) -> None:
    logger = build(tmp_path)
    for index in range(MAX_EVENTS + 5):
        dropped = logger.record(
            Event(kind=EventKind.AUDIT, source="test", message=str(index))
        )
    assert dropped == 1
    assert len(logger.events()) == MAX_EVENTS
    assert logger.events()[0].message == "5"
    assert logger.store.exists(KEY_EVENTS)
    assert logger.flush() == 0


def test_restore_reloads_the_log(tmp_path) -> None:
    logger = build(tmp_path)
    logger.record(Event(kind=EventKind.ARC, source="weld", message="struck"))
    logger.record(Event(kind=EventKind.STOP, source="line", message="stopped"))
    other = build(tmp_path)
    assert other.restore() == 2
    assert [event.message for event in other.events()] == ["struck", "stopped"]


def test_restore_of_an_empty_log(tmp_path) -> None:
    assert build(tmp_path).restore() == 0


def test_query_and_recent(tmp_path) -> None:
    logger = build(tmp_path)
    for index in range(6):
        logger.record(Event(kind=EventKind.TRACK, source="strip", message=f"t{index}"))
    logger.record(Event(kind=EventKind.STOP, source="line", message="stop"))
    assert [event.message for event in logger.query(EventKind.TRACK, 2)] == ["t5", "t4"]
    assert len(logger.query(EventKind.TRACK)) == 6
    assert logger.recent(0) == []
    assert logger.recent(2)[-1].message == "stop"
    assert logger.recent(100)[0].message == "t0"


def test_alarm_register(tmp_path) -> None:
    logger = build(tmp_path)
    logger.raise_alarm("weld-overcurrent")
    logger.raise_alarm("tank-low")
    assert logger.active_alarms() == ["tank-low", "weld-overcurrent"]
    assert logger.alarm_active("tank-low") is True
    assert logger.clear_alarm("tank-low") is True
    assert logger.clear_alarm("tank-low") is False
    assert logger.active_alarms() == ["weld-overcurrent"]


def test_summary_counts_by_kind(tmp_path) -> None:
    logger = build(tmp_path)
    logger.record(Event(kind=EventKind.ARC, source="weld"))
    logger.record(Event(kind=EventKind.ARC, source="weld"))
    logger.record(Event(kind=EventKind.STOP, source="line"))
    assert logger.summary() == {"arc": 2, "stop": 1}


def test_handles_are_unique(tmp_path) -> None:
    logger = build(tmp_path)
    assert logger.new_handle() != logger.new_handle()


def test_snapshot_view(tmp_path) -> None:
    logger = build(tmp_path)
    logger.record(Event(kind=EventKind.PUMP, source="pump", message="started"))
    logger.raise_alarm("a1")
    view = logger.snapshot()
    assert view["alarms"] == ["a1"]
    assert view["summary"] == {"pump": 1}
    assert view["events"][0]["message"] == "started"
