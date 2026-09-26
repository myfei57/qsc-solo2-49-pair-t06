"""Exit section: exhaust, rolls, shear and coil change."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.records import TrackSnapshot
from linecontrol.exit.errors import ExitError, ExitErrorCode
from linecontrol.exit.section import Exit
from linecontrol.pickle.tank import Tank
from linecontrol.store.filestore import FileStore
from linecontrol.strip.strip import Strip


def build(tmp_path) -> Exit:
    store = FileStore(tmp_path)
    bus = EventBus()
    tank = Tank(store, bus)
    strip = Strip(store, bus, lambda: 1.0, tank.flushed)
    return Exit(tank, strip, bus)


def with_track(section: Exit, position: float = 120.0) -> None:
    section.strip.restore_track(TrackSnapshot(position=position, seam_id="seam-1"))


def test_exhaust_establish_and_reset(tmp_path) -> None:
    section = build(tmp_path)
    assert section.exhaust_ok() is False
    section.exhaust_establish()
    assert section.exhaust_ok() is True
    section.exhaust_reset()
    assert section.exhaust_ok() is False


def test_roll_lift_is_blocked_while_rinsing(tmp_path) -> None:
    section = build(tmp_path)
    section.tank.rinse()
    with pytest.raises(ExitError) as caught:
        section.squeeze_roll_lift()
    assert caught.value.code is ExitErrorCode.RINSE_ACTIVE
    with pytest.raises(ExitError):
        section.recover_lift()
    section.tank.rinse_stop()
    section.squeeze_roll_lift()
    assert section.roll_up() is True
    section.squeeze_roll_down()
    assert section.roll_up() is False
    section.recover_lift()
    assert section.roll_up() is True


def test_shear_requires_a_fresh_track(tmp_path) -> None:
    section = build(tmp_path)
    with pytest.raises(ExitError) as caught:
        section.shear()
    assert caught.value.code is ExitErrorCode.TRACK_STALE
    with_track(section)
    section.set_shear_offset(2.5)
    assert section.shear_offset() == pytest.approx(2.5)
    assert section.shear() == pytest.approx(122.5)
    assert section.last_shear() == pytest.approx(122.5)


def test_coil_change_runs_rinse_roll_shear_in_order(tmp_path) -> None:
    section = build(tmp_path)
    section.tank.rinse()
    with_track(section)
    position = section.coil_change()
    assert section.tank.rinsing() is False
    assert section.roll_up() is True
    assert position == pytest.approx(120.0)


def test_coil_change_stops_at_a_stale_track(tmp_path) -> None:
    section = build(tmp_path)
    section.tank.rinse()
    with pytest.raises(ExitError) as caught:
        section.coil_change()
    assert caught.value.code is ExitErrorCode.TRACK_STALE
    assert section.tank.rinsing() is False
    assert section.roll_up() is True
    assert section.last_shear() == pytest.approx(0.0)


def test_taper_setpoint_and_weight(tmp_path) -> None:
    section = build(tmp_path)
    assert section.taper_setpoint(50.0, 0.0) == pytest.approx(50.0)
    assert section.taper_setpoint(50.0, 100.0) == pytest.approx(50.0)
    assert section.taper() == pytest.approx(50.0)
    weight = section.coil_weight(2.5, 2.3, 1250.0, 4200.0)
    assert weight > 0.0


def test_snapshot_and_sequence_reset(tmp_path) -> None:
    section = build(tmp_path)
    section.exhaust_establish()
    with_track(section)
    section.shear()
    view = section.snapshot()
    assert view["exhaust"] is True
    assert view["shear"] == pytest.approx(120.0)
    section.data.reset_sequence()
    assert section.exhaust_ok() is False
    assert section.roll_up() is False
    assert section.last_shear() == pytest.approx(0.0)
