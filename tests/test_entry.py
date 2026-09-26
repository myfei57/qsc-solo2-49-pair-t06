"""Entry section behaviour."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.events import Event
from linecontrol.domain.kinds import EventKind
from linecontrol.entry.controller import Controller
from linecontrol.entry.errors import EntryError, EntryErrorCode


def build() -> Controller:
    return Controller(EventBus())


def test_load_requires_a_coil_id() -> None:
    controller = build()
    with pytest.raises(EntryError) as caught:
        controller.load_coil("", 10.0)
    assert caught.value.code is EntryErrorCode.NO_COIL


def test_align_confirm_needs_a_loaded_coil() -> None:
    controller = build()
    with pytest.raises(EntryError):
        controller.align_confirm()
    controller.load_coil("C-1", 40.0)
    controller.align_confirm()
    assert controller.confirm().ok
    assert controller.confirm().position == pytest.approx(40.0)


def test_align_refresh_replaces_the_confirmation() -> None:
    controller = build()
    controller.load_coil("C-1", 40.0)
    controller.align_confirm()
    controller.align_refresh(57.5)
    assert controller.confirm().position == pytest.approx(57.5)
    assert controller.confirm_state().position == pytest.approx(57.5)


def test_centring_correction_is_bounded() -> None:
    controller = build()
    controller.load_coil("C-1", 30.0)
    assert controller.center_error() == pytest.approx(30.0)
    assert controller.correction() == pytest.approx(2.0)
    controller.align_offset(-31.0)
    assert controller.correction() == pytest.approx(-1.0)


def test_correct_head_moves_the_head_by_the_correction() -> None:
    controller = build()
    controller.load_coil("C-1", 5.0)
    applied = controller.correct_head()
    assert applied == pytest.approx(2.0)
    assert controller.head_position() == pytest.approx(2.0)


def test_sample_window_and_settle() -> None:
    controller = build()
    controller.load_coil("C-1", 0.0)
    assert controller.sample_settle() == 0.0
    for value in range(20):
        controller.push_sample(float(value))
    assert controller.sample_count() == 12
    assert controller.moving_average() == pytest.approx(13.5)
    assert controller.sample_settle() == pytest.approx(13.5)


def test_splice_release_follows_the_interlock_and_alarm() -> None:
    bus = EventBus()
    controller = Controller(bus)
    controller.load_coil("C-1", 10.0)
    held = {"value": False}
    controller.set_interlock_provider(lambda: held["value"])
    with pytest.raises(EntryError) as caught:
        controller.splice_release()
    assert caught.value.code is EntryErrorCode.INTERLOCK_HELD
    held["value"] = True
    controller.splice_release()
    bus.publish(Event(kind=EventKind.ALARM, source="weld", message="overcurrent"))
    assert controller.alarm_seen() is True
    with pytest.raises(EntryError) as caught:
        controller.splice_release()
    assert caught.value.code is EntryErrorCode.ALARM_ACTIVE
    bus.publish(Event(kind=EventKind.LATCH, source="weld", message="released"))
    assert controller.alarm_seen() is False
    controller.splice_release()


def test_coil_change_clears_the_head_state() -> None:
    controller = build()
    controller.load_coil("C-1", 12.0)
    controller.align_confirm()
    controller.track_head(4.0)
    controller.coil_change()
    assert controller.coil_id() == ""
    assert controller.head_position() == 0.0
    assert controller.confirm().ok is False
    with pytest.raises(EntryError):
        controller.coil_change()


def test_snapshot_reports_the_entry_view() -> None:
    controller = build()
    controller.load_coil("C-1", 20.0)
    controller.align_confirm()
    controller.push_sample(20.0)
    view = controller.snapshot()
    assert view["coil"] == "C-1"
    assert view["aligned"] is True
    assert view["sampleCount"] == 1
