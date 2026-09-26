"""Tension setpoint, gain calibration and the speed ramp."""

from __future__ import annotations

import pytest

from linecontrol.domain.records import TensionSnapshot, utcnow
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import KEY_GAIN, KEY_TENSION
from linecontrol.store.snapshot import save_json
from linecontrol.tension.errors import TensionError, TensionErrorCode
from linecontrol.tension.roller import Roller
from linecontrol.tension.state import SpeedState, SpeedStep


def build(tmp_path) -> Roller:
    return Roller(FileStore(tmp_path))


def test_gain_calibration_persists_only_on_change(tmp_path) -> None:
    roller = build(tmp_path)
    assert roller.recalibrate(1.0) is False
    assert roller.recalibrate(1.2) is True
    assert roller.store.exists(KEY_GAIN)
    assert roller.gain() == pytest.approx(1.2)
    with pytest.raises(TensionError) as caught:
        roller.recalibrate(0.0)
    assert caught.value.code is TensionErrorCode.INVALID_GAIN


def test_effective_tension_follows_the_gain(tmp_path) -> None:
    roller = build(tmp_path)
    roller.apply_setpoint(80.0)
    roller.recalibrate(1.25)
    assert roller.data.effective_tension() == pytest.approx(100.0)


def test_speed_up_requires_a_persisted_tension(tmp_path) -> None:
    roller = build(tmp_path)
    with pytest.raises(TensionError) as caught:
        roller.allow_speedup()
    assert caught.value.code is TensionErrorCode.NOT_PERSISTED
    save_json(
        roller.store,
        KEY_TENSION,
        TensionSnapshot(value=93.0, gain=1.1, saved=utcnow()),
    )
    snapshot = roller.allow_speedup()
    assert snapshot.value == pytest.approx(93.0)
    assert roller.setpoint() == pytest.approx(93.0)
    assert roller.gain() == pytest.approx(1.1)
    assert roller.speed_permitted() is True
    assert roller.speed() == SpeedState.RUNNING


def test_ramp_plan_scales_with_the_target(tmp_path) -> None:
    roller = build(tmp_path)
    save_json(roller.store, KEY_TENSION, TensionSnapshot(value=88.0, saved=utcnow()))
    roller.allow_speedup()
    short = roller.plan_speedup(1.5)
    assert len(short.steps) == 3
    assert short.steps[-1].speed == pytest.approx(1.5)
    long = roller.plan_speedup(3.0)
    assert len(long.steps) == 5
    for step in long.steps:
        roller.apply_step(step)
    assert roller.speed() in {SpeedState.RUNNING, SpeedState.FULL}


def test_ramp_requires_persistence_and_positive_target(tmp_path) -> None:
    roller = build(tmp_path)
    with pytest.raises(TensionError) as caught:
        roller.plan_speedup(0.0)
    assert caught.value.code is TensionErrorCode.INVALID_SPEED
    with pytest.raises(TensionError) as caught:
        roller.plan_speedup(2.0)
    assert caught.value.code is TensionErrorCode.RAMP_UNREADY


def test_apply_step_requires_a_ready_roller(tmp_path) -> None:
    roller = build(tmp_path)
    with pytest.raises(TensionError) as caught:
        roller.apply_step(SpeedStep(speed=1.0, setpoint=80.0, step_index=1))
    assert caught.value.code is TensionErrorCode.RAMP_UNREADY


def test_restore_tension_rebuilds_the_setpoint(tmp_path) -> None:
    roller = build(tmp_path)
    roller.restore_tension(TensionSnapshot(value=70.0, gain=1.3, saved=utcnow()))
    assert roller.setpoint() == pytest.approx(70.0)
    assert roller.gain() == pytest.approx(1.3)
    assert roller.speed_permitted() is True
    empty = build(tmp_path / "other")
    empty.restore_tension(TensionSnapshot(value=0.0, saved=utcnow()))
    assert empty.speed_permitted() is False


def test_snapshot_exposes_the_speed_machine(tmp_path) -> None:
    roller = build(tmp_path)
    view = roller.snapshot()
    assert view["speed"] == SpeedState.STANDBY
    assert view["transitions"] == [SpeedState.STANDBY]
