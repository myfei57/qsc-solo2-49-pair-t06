"""Pickling tank level, calibration and dosing."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.records import AcidSnapshot
from linecontrol.pickle.errors import PickleError, PickleErrorCode
from linecontrol.pickle.tank import Tank
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import KEY_ACID
from linecontrol.store.snapshot import load_json


def build(tmp_path) -> Tank:
    return Tank(FileStore(tmp_path), EventBus())


def test_level_gate_tracks_the_minimum(tmp_path) -> None:
    tank = build(tmp_path)
    tank.level_check(2.0)
    assert tank.level_ok() is False
    tank.level_check(3.1)
    assert tank.level_ok() is True
    assert tank.minimum_level() == pytest.approx(2.5)


def test_calibration_shifts_the_concentration(tmp_path) -> None:
    tank = build(tmp_path)
    tank.level_check(10.0)
    tank.calibrate(1.5)
    assert tank.offset() == pytest.approx(1.5)
    assert tank.concentration() == pytest.approx(11.5)
    assert tank.store.exists(KEY_ACID)


def test_calibration_rejects_an_out_of_range_offset(tmp_path) -> None:
    tank = build(tmp_path)
    with pytest.raises(PickleError) as caught:
        tank.calibrate(120.0)
    assert caught.value.code is PickleErrorCode.OFFSET_INVALID


def test_dosing_plan_and_application(tmp_path) -> None:
    tank = build(tmp_path)
    tank.level_check(4.0)
    plan = tank.plan_dose(volume=20.0, target=10.0)
    assert plan.required is True
    assert plan.dose == pytest.approx(120.0)
    tank.apply_dose(plan.dose, 20.0)
    assert tank.concentration() == pytest.approx(10.0)
    assert tank.plan_dose(20.0, 10.0).required is False
    with pytest.raises(PickleError) as caught:
        tank.dose_volume(0.0, 10.0)
    assert caught.value.code is PickleErrorCode.TANK_VOLUME
    tank.apply_dose(5.0, 0.0)
    assert tank.concentration() == pytest.approx(10.0)


def test_rinse_valve_and_flush(tmp_path) -> None:
    tank = build(tmp_path)
    tank.rinse()
    assert tank.rinsing() is True
    assert tank.flushed() is False
    snapshot, ok = tank.rinse_persisted()
    assert ok is True and snapshot.active is True
    tank.rinse_flush()
    assert tank.flushed() is True
    tank.rinse_stop()
    assert tank.rinsing() is False
    other = build(tmp_path / "restore")
    other.restore_rinse(True)
    assert other.rinsing() is True


def test_acid_snapshot_restore(tmp_path) -> None:
    tank = build(tmp_path)
    tank.level_check(6.0)
    tank.calibrate(-0.5)
    snapshot, ok = load_json(tank.store, KEY_ACID, AcidSnapshot)
    assert ok is True
    fresh = build(tmp_path / "fresh")
    fresh.restore_acid(snapshot)
    assert fresh.level() == pytest.approx(6.0)
    assert fresh.offset() == pytest.approx(-0.5)


def test_level_trend_reports_the_direction(tmp_path) -> None:
    tank = build(tmp_path)
    for value in (1.0, 1.0, 3.0, 3.0):
        tank.level_check(value)
    assert tank.level_trend() == pytest.approx(2.0)
    assert tank.data.trend == [1.0, 1.0, 3.0, 3.0]


def test_snapshot_reports_the_tank_view(tmp_path) -> None:
    tank = build(tmp_path)
    tank.level_check(4.0)
    tank.rinse()
    view = tank.snapshot()
    assert view["level"] == pytest.approx(4.0)
    assert view["rinsing"] is True
    assert view["rinsingPersist"] is True
