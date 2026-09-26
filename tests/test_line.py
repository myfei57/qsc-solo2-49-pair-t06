"""Cross-area call chains on the line controller."""

from __future__ import annotations

import pytest

from linecontrol.domain.kinds import EventKind
from linecontrol.domain.phase import Phase
from linecontrol.entry.errors import EntryError
from linecontrol.line.machine import Line
from linecontrol.line.workflow import CycleInput
from linecontrol.pump.errors import PumpError


def test_default_state(line: Line) -> None:
    state = line.state()
    assert state["phase"] == Phase.IDLE.value
    assert state["weld"]["state"] == "idle"
    assert state["tension"]["setpoint"] == pytest.approx(80.0)
    assert state["pickle"]["minLevel"] == pytest.approx(2.5)
    assert state["alarms"] == []


def test_weld_and_speedup_runs_the_full_chain(line: Line) -> None:
    line.load_coil("C-1", 92.0)
    line.weld_and_speedup()
    assert line.phase is Phase.ACID_LOOP
    assert line.weld.state() == "spliced"
    assert line.tension.speed_permitted() is True
    assert line.store.exists("weld.record")
    assert line.store.exists("tension.current")
    assert line.strip.track_position() == pytest.approx(line.weld.track_point())
    names = [step["name"] for step in line.sequence_snapshot()["steps"]]
    assert names[:3] == ["align-confirm", "arc-gate", "arc"]
    assert "tension-persist" in names
    assert names.index("tension-persist") < names.index("speedup")


def test_weld_and_speedup_requires_a_coil(line: Line) -> None:
    with pytest.raises(EntryError):
        line.weld_and_speedup()
    assert line.phase is Phase.FAULT
    failures = line.sequence_failures()
    assert failures[-1]["name"] == "aborted"


def test_speedup_is_refused_without_a_persisted_tension(line: Line) -> None:
    line.load_coil("C-1", 90.0)
    line.entry.align_confirm()
    line.weld.gate_arc()
    line.weld.arc()
    line.weld.splice()
    with pytest.raises(Exception):
        line.tension.allow_speedup()


def test_acid_loop_gates_on_the_level(line: Line) -> None:
    line.load_coil("C-1", 90.0)
    line.weld_and_speedup()
    with pytest.raises(PumpError):
        line.start_acid_loop(1.0)
    assert line.pump.running() is False
    assert line.sequence_failures()[-1]["name"] == "aborted"
    line.start_acid_loop(4.5)
    assert line.pump.running() is True
    assert line.pickle.rinsing() is True
    assert line.exit.roll_up() is False


def test_splice_refresh_moves_the_track(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    line.set_strip_speed(1.4)
    line.splice_and_refresh(95.0)
    assert line.weld.track_point() == pytest.approx(95.0)
    assert line.strip.track_position() == pytest.approx(95.0)
    assert line.strip.seam_id() == line.weld.seam_id()


def test_resume_acid_loop_rechecks_the_level(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    line.start_acid_loop(4.6)
    line.stop_line()
    with pytest.raises(PumpError):
        line.resume_acid_loop(0.5)
    line.resume_acid_loop(4.6)
    assert line.pump.running() is True


def test_stop_sequence_order(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    line.start_acid_loop(4.6)
    line.stop_line()
    names = [step["name"] for step in line.sequence_snapshot()["steps"]]
    assert names.index("strip-stop") < names.index("pump-stop")
    assert line.pump.running() is False
    assert line.strip.stopped() is True
    assert line.strip.tail_dirty() is False
    assert line.exit.exhaust_ok() is False


def test_heat_dryer_and_coil(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    line.start_acid_loop(4.6)
    line.set_strip_speed(1.5)
    line.splice_and_refresh(90.0)
    line.heat_dryer_and_coil()
    assert line.dry.data.heating() is True
    assert line.phase is Phase.COIL_DONE
    assert line.entry.coil_id() == ""


def test_coil_change_requires_a_coil(line: Line) -> None:
    with pytest.raises(Exception):
        line.coil_change()
    assert line.phase is Phase.FAULT


def test_production_cycle_runs_to_completion(line: Line) -> None:
    payload = CycleInput(
        coil_id="C-2601",
        target=95.0,
        level=4.4,
        voltage=24.0,
        current=300.0,
        speed=1.5,
    )
    line.production_cycle(payload)
    assert line.phase is Phase.IDLE
    assert line.coil_no == 1
    assert line.handle
    labels = line.sequence_snapshot()["label"]
    assert labels == "production"
    assert not line.sequence_failures()
    assert line.weld.state() == "spliced"
    assert len(line.weld_seams(10)) == 2


def test_alarm_and_clear_pair(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.alarm_overcurrent()
    assert line.audit.active_alarms() == ["weld-overcurrent"]
    assert line.weld.interlock_ok() is False
    assert line.last_backup is not None
    with pytest.raises(Exception):
        line.splice_release()
    assert line.clear_weld_alarm() is True
    assert line.audit.active_alarms() == []
    line.splice_release()


def test_commands_forward_to_the_areas(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    assert line.recalibrate_tension(1.1) is True
    assert line.tension.gain() == pytest.approx(1.1)
    assert line.correct_head() == pytest.approx(2.0)
    line.align_offset(-4.0)
    assert line.entry.center_error() == pytest.approx(54.0)
    line.track_head(6.0)
    assert line.entry.head_position() == pytest.approx(8.0)
    line.push_head_sample(8.0)
    assert line.entry.sample_count() == 1
    line.set_strip_speed(2.0)
    assert line.advance_strip(5.0) == pytest.approx(5.0)
    assert line.track_eta(105.0) == pytest.approx(50.0)
    assert line.sag() == pytest.approx(1.0)
    line.set_shear_offset(1.5)
    assert line.exit.shear_offset() == pytest.approx(1.5)
    assert line.coil_weight(2.5, 2.3, 1200.0, 4000.0) > 0.0
    assert line.taper_exit(40.0, 120.0) == pytest.approx(40.0 * (0.6 + 0.4 * 1.2))
    line.set_dryer_dew(10.0)
    assert line.dry.dew_point() == pytest.approx(10.0)
    assert line.set_dryer_heat(150.0) == pytest.approx(15.0)


def test_replenish_and_ramp_paths(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    line.start_acid_loop(4.0)
    plan = line.replenish_acid(20.0, 12.0)
    assert plan.required is True
    assert line.pickle.concentration() > 4.0
    line.pickle.level_check(12.0)
    with pytest.raises(PumpError):
        line.replenish_acid(20.0, 5.0)
    ramp = line.ramp_speed(2.4)
    assert len(ramp.steps) == 5
    assert line.tension.speed() in {"running", "full"}


def test_audit_query_and_kinds(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    events = line.audit_query(EventKind.ARC, 5)
    assert events and events[0].kind is EventKind.ARC
    recent = line.audit_query(None, 5)
    assert len(recent) == 5
    summary = line.audit.summary()
    assert summary["arc"] >= 1
    assert summary["weld"] >= 1


def test_run_report_and_store_view(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    report = line.run_report()
    assert report["coil"] == "C-1"
    assert report["weldKnown"] is True
    assert report["dataDir"]
    assert report["bus"]["delivered"] >= 1
    assert "pumpPersistOk" in report
    line.alarm_overcurrent()
    assert line.run_report()["lastBackup"]["count"] >= 1


def test_sequence_clear(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    assert line.sequence_snapshot()["steps"]
    line.clear_sequence()
    assert line.sequence_snapshot()["steps"] == []


def test_machines_are_reported(line: Line) -> None:
    line.load_coil("C-1", 60.0)
    line.weld_and_speedup()
    assert line.weld.machine.history() == ("idle", "gated", "welding", "spliced")
    assert line.tension.data.machine.state in {"running", "full"}
