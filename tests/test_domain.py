"""Value types, enumerations and the state machine primitive."""

from __future__ import annotations

import pytest

from linecontrol.domain.events import Event, utcnow
from linecontrol.domain.kinds import STREAM_KINDS, EventKind
from linecontrol.domain.machine import IllegalTransition, StateMachine
from linecontrol.domain.phase import Phase
from linecontrol.domain.records import LatchSnapshot, TensionSnapshot


def test_event_round_trip_preserves_fields() -> None:
    event = Event(kind=EventKind.ARC, source="weld", message="struck", payload=12.5)
    restored = Event.from_dict(event.to_dict())
    assert restored.kind is EventKind.ARC
    assert restored.source == "weld"
    assert restored.message == "struck"
    assert restored.payload == pytest.approx(12.5)
    assert restored.at == event.at


def test_event_from_dict_defaults_unknown_timestamp() -> None:
    restored = Event.from_dict({"kind": "stop", "message": "stopped"})
    assert restored.kind is EventKind.STOP
    assert restored.payload == 0.0
    assert restored.at.tzinfo is not None


def test_state_machine_rejects_a_forbidden_jump() -> None:
    machine = StateMachine("demo", "a", {"a": {"b"}, "b": {"a"}})
    with pytest.raises(IllegalTransition) as caught:
        machine.enter("c")
    assert caught.value.machine == "demo"
    assert machine.state == "a"


def test_state_machine_force_records_history() -> None:
    machine = StateMachine("demo", "a", {"a": {"b"}, "b": {"a"}})
    machine.force("b")
    assert machine.state == "b"
    assert machine.history() == ("a", "b")
    assert machine.reachable() == ("a",)


def test_state_machine_rejects_unknown_initial_state() -> None:
    with pytest.raises(ValueError):
        StateMachine("demo", "missing", {"a": {"b"}})


def test_stream_kinds_cover_every_event_kind() -> None:
    assert set(STREAM_KINDS) == set(EventKind)


def test_snapshot_records_round_trip() -> None:
    latch = LatchSnapshot(interlock=True, alarm=True)
    assert LatchSnapshot.from_dict(latch.to_dict()) == latch
    tension = TensionSnapshot(value=91.0, gain=1.2)
    assert TensionSnapshot.from_dict(tension.to_dict()) == tension


def test_phase_values_are_stable_strings() -> None:
    assert Phase.ACID_LOOP.value == "acid-loop"
    assert str(Phase.FAULT) == "fault"


def test_utcnow_is_timezone_aware() -> None:
    assert utcnow().tzinfo is not None
