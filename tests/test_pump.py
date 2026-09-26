"""Circulation pump gating, run hours and persistence."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.records import PumpSnapshot
from linecontrol.pickle.tank import Tank
from linecontrol.pump.errors import PumpError, PumpErrorCode
from linecontrol.pump.pump import Pump
from linecontrol.pump.state import PumpState
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import KEY_HOURS, KEY_PUMP


class StripFlag:
    def __init__(self, stopped: bool) -> None:
        self.stopped = stopped

    def __call__(self) -> bool:
        return self.stopped


def build(tmp_path, stopped: bool = True) -> Pump:
    store = FileStore(tmp_path)
    bus = EventBus()
    tank = Tank(store, bus)
    return Pump(tank, store, bus, StripFlag(stopped))


def test_start_refuses_a_low_level(tmp_path) -> None:
    pump = build(tmp_path)
    pump.tank.level_check(1.0)
    with pytest.raises(PumpError) as caught:
        pump.start_gate()
    assert caught.value.code is PumpErrorCode.LEVEL_LOW
    with pytest.raises(PumpError):
        pump.start()
    assert pump.running() is False


def test_start_and_resume_both_gate_on_the_level(tmp_path) -> None:
    pump = build(tmp_path)
    pump.tank.level_check(4.0)
    pump.start()
    assert pump.running() is True
    assert pump.tank.level() == pytest.approx(4.0)
    pump.stop()
    pump.tank.level_check(1.2)
    with pytest.raises(PumpError) as caught:
        pump.resume()
    assert caught.value.code is PumpErrorCode.LEVEL_LOW
    pump.tank.level_check(3.0)
    pump.resume()
    assert pump.running() is True


def test_stop_requires_a_stopped_strip(tmp_path) -> None:
    pump = build(tmp_path, stopped=False)
    pump.tank.level_check(4.0)
    pump.start()
    with pytest.raises(PumpError) as caught:
        pump.stop_gate()
    assert caught.value.code is PumpErrorCode.STRIP_RUN
    snap, ok = pump.persisted()
    assert ok is True and snap.running is True
    assert pump.running() is True


def test_run_hours_accumulate_on_stop(tmp_path) -> None:
    pump = build(tmp_path)
    pump.tank.level_check(4.0)
    pump.start()
    assert pump.started_at() is not None
    pump.stop()
    assert pump.store.exists(KEY_HOURS)
    assert pump.started_at() is None
    assert pump.persisted_hours() == pytest.approx(pump.run_seconds())
    pump.record_run(30.0)
    assert pump.run_seconds() >= 30.0
    assert pump.persisted_hours() == pytest.approx(pump.run_seconds())
    assert pump.data.machine.state == PumpState.STOPPED


def test_replenish_gate_uses_the_calibrated_concentration(tmp_path) -> None:
    pump = build(tmp_path)
    pump.tank.level_check(4.0)
    pump.tank.calibrate(1.0)
    with pytest.raises(PumpError) as caught:
        pump.replenish_gate(3.0)
    assert caught.value.code is PumpErrorCode.NO_REPLENISH
    pump.replenish_gate(10.0)


def test_state_snapshot_restore(tmp_path) -> None:
    pump = build(tmp_path)
    pump.restore(PumpSnapshot(running=True))
    assert pump.running() is True
    pump.restore(PumpSnapshot(running=False))
    assert pump.running() is False
    pump.restore_run(3600.0)
    assert pump.run_seconds() == pytest.approx(3600.0)
    assert pump.store.exists(KEY_PUMP) is False


def test_snapshot_view(tmp_path) -> None:
    pump = build(tmp_path)
    pump.tank.level_check(4.0)
    pump.start()
    view = pump.snapshot()
    assert view["running"] is True
    assert view["persisted"] is True
    assert view["startedAt"] is not None
    assert view["transitions"] == [PumpState.STOPPED, PumpState.RUNNING]
