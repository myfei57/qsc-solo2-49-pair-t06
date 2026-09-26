"""Line sequence bookkeeping."""

from __future__ import annotations

from linecontrol.line.sequence import Sequence


def test_sequence_records_steps_and_failures() -> None:
    sequence = Sequence()
    sequence.begin("demo")
    sequence.record("one")
    sequence.record("two", RuntimeError("boom"))
    snapshot = sequence.snapshot()
    assert snapshot["label"] == "demo"
    assert snapshot["started"] is not None
    assert [step["name"] for step in snapshot["steps"]] == ["one", "two"]
    assert [step["ok"] for step in snapshot["steps"]] == [True, False]
    assert snapshot["steps"][1]["detail"] == "boom"
    assert len(sequence.failures()) == 1


def test_begin_if_idle_keeps_the_running_label() -> None:
    sequence = Sequence()
    sequence.begin_if_idle("outer")
    sequence.begin_if_idle("inner")
    assert sequence.label() == "outer"
    sequence.clear()
    assert sequence.label() == ""
    sequence.begin_if_idle("inner")
    assert sequence.label() == "inner"
    assert sequence.snapshot()["started"] is not None


def test_begin_replaces_the_previous_run() -> None:
    sequence = Sequence()
    sequence.begin("first")
    sequence.record("a")
    sequence.begin("second")
    assert sequence.snapshot()["steps"] == []
    assert sequence.label() == "second"


def test_clear_resets_the_started_stamp() -> None:
    sequence = Sequence()
    sequence.begin("demo")
    sequence.record("a")
    sequence.clear()
    snapshot = sequence.snapshot()
    assert snapshot["started"] is None
    assert snapshot["steps"] == []
