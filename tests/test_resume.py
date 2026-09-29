"""Resuming an interrupted production cycle from its checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linecontrol.domain.records import CycleCheckpoint, utcnow
from linecontrol.line.errors import LineError, LineErrorCode
from linecontrol.line.machine import Line
from linecontrol.line.workflow import CycleInput
from linecontrol.store.keys import KEY_CYCLE
from linecontrol.store.snapshot import save_json

PAYLOAD = CycleInput(
    coil_id="C-77",
    target=95.0,
    level=4.4,
    voltage=24.0,
    current=300.0,
    speed=1.5,
)


def _checkpoint(line: Line) -> dict[str, object]:
    raw = line.store.load(KEY_CYCLE)
    assert raw is not None
    return json.loads(raw.decode("utf-8"))


def _seed_checkpoint(line: Line, stage: int, seams: int = 0) -> None:
    save_json(
        line.store,
        KEY_CYCLE,
        CycleCheckpoint(
            stage=stage,
            coil_id=PAYLOAD.coil_id,
            target=PAYLOAD.target,
            level=PAYLOAD.level,
            voltage=PAYLOAD.voltage,
            current=PAYLOAD.current,
            speed=PAYLOAD.speed,
            coil_no=line.coil_no,
            handle=line.handle,
            seams=seams,
            saved=utcnow(),
        ),
    )


def test_a_completed_cycle_leaves_no_checkpoint(line: Line) -> None:
    line.production_cycle(PAYLOAD)
    assert line.store.exists(KEY_CYCLE) is False


def test_checkpoint_is_written_before_the_first_stage(line: Line) -> None:
    seen: list[int] = []
    original = line.entry.load_coil

    def fail_load(coil_id: str, target: float) -> None:
        seen.append(_checkpoint(line)["stage"])
        raise RuntimeError("coil cart jammed")

    line.entry.load_coil = fail_load  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        line.production_cycle(PAYLOAD)
    line.entry.load_coil = original  # type: ignore[method-assign]

    assert seen == [0]
    assert _checkpoint(line)["stage"] == 0
    report = line.resume_cycle(PAYLOAD)
    assert report.completed is True
    assert line.phase.value == "idle"
    assert line.store.exists(KEY_CYCLE) is False


def test_resume_continues_from_the_interrupted_stage(line: Line) -> None:
    # Reach the boundary after the acid-loop stage, then plant the checkpoint
    # the driver would have written there.
    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    line.weld_and_speedup()
    line.start_acid_loop(PAYLOAD.level)
    _seed_checkpoint(line, stage=3, seams=1)

    seams_before = len(line.weld_seams(0))
    report = line.resume_cycle(PAYLOAD)

    assert report.stage == 3
    assert seams_before == 1
    assert len(line.weld_seams(0)) == 2  # only splice-refresh adds a seam
    assert line.phase.value == "idle"
    assert line.store.exists(KEY_CYCLE) is False


def test_resume_without_a_checkpoint_is_refused(line: Line) -> None:
    with pytest.raises(LineError) as raised:
        line.resume_cycle(PAYLOAD)
    assert raised.value.code is LineErrorCode.NO_CHECKPOINT


def test_lost_precondition_scraps_the_whole_run(line: Line) -> None:
    from linecontrol.domain.machine import IllegalTransition

    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    line.weld_and_speedup()
    line.start_acid_loop(PAYLOAD.level)
    _seed_checkpoint(line, stage=3, seams=1)

    # The acid premise is gone: the pump tripped while the line was down.
    line.pump.data.machine.force("stopped")

    with pytest.raises(LineError) as raised:
        line.resume_cycle(PAYLOAD)
    assert raised.value.code is LineErrorCode.PRECONDITION_LOST
    assert "pump-running" in raised.value.detail
    assert line.phase.value == "fault"
    # The partial run is scrapped: nothing left to resume from.
    assert line.store.exists(KEY_CYCLE) is False

    # "Continue" is now impossible: the welder still stands on the old seam and
    # a start-over cannot strike a fresh arc without a manual reset.  The point
    # is that the operator can no longer accidentally half-continue.
    with pytest.raises(IllegalTransition):
        line.production_cycle(PAYLOAD)


def test_scrapped_run_can_be_started_over_after_a_manual_reset(
    line: Line,
) -> None:
    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    line.weld_and_speedup()
    line.start_acid_loop(PAYLOAD.level)
    _seed_checkpoint(line, stage=3, seams=1)
    line.pump.data.machine.force("stopped")

    with pytest.raises(LineError):
        line.resume_cycle(PAYLOAD)

    # Maintenance clears the line back to a known-good starting point, then the
    # full cycle runs again from stage 0 with a fresh coil number.  Only the
    # seams welded by the new cycle are added on top of the abandoned one.
    line.weld.machine.force("idle")
    line.tension.data.machine.force("standby")
    line.production_cycle(PAYLOAD)
    assert line.phase.value == "idle"
    assert line.coil_no == 2
    assert len(line.weld_seams(0)) == 3
    assert line.store.exists(KEY_CYCLE) is False


def test_resume_rejects_a_changed_input(line: Line) -> None:
    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    _seed_checkpoint(line, stage=1)

    changed = CycleInput(
        coil_id=PAYLOAD.coil_id,
        target=70.0,
        level=PAYLOAD.level,
        voltage=PAYLOAD.voltage,
        current=PAYLOAD.current,
        speed=PAYLOAD.speed,
    )
    with pytest.raises(LineError) as raised:
        line.resume_cycle(changed)
    assert raised.value.code is LineErrorCode.PRECONDITION_LOST
    assert "input:target" in raised.value.detail
    assert line.store.exists(KEY_CYCLE) is False


def test_a_missing_coil_premise_scraps_a_stage_one_resume(line: Line) -> None:
    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    _seed_checkpoint(line, stage=1)

    # The coil was removed by maintenance during the interruption.
    line.entry.state.clear_coil()

    with pytest.raises(LineError) as raised:
        line.resume_cycle(PAYLOAD)
    assert raised.value.code is LineErrorCode.PRECONDITION_LOST
    assert "coil-loaded" in raised.value.detail


def _reach(line: Line, stage: int) -> None:
    line.load_coil(PAYLOAD.coil_id, PAYLOAD.target)
    if stage == 1:
        return
    line.weld_and_speedup()
    if stage == 2:
        return
    line.start_acid_loop(PAYLOAD.level)
    if stage == 3:
        return
    line.set_strip_speed(PAYLOAD.speed)
    if stage == 4:
        return
    line.set_weld_power(PAYLOAD.voltage, PAYLOAD.current)
    if stage == 5:
        return
    line.splice_and_refresh(PAYLOAD.target + 30)
    if stage == 6:
        return
    line.heat_dryer_and_coil()


def test_resume_at_the_final_stop_boundary(line: Line) -> None:
    # Everything except stop_line has run.  The coil change already closed the
    # rinse, lifted the rolls, changed the coil and reset the exit exhaust.
    _reach(line, 7)
    _seed_checkpoint(line, stage=7, seams=2)

    assert line.entry.coil_id() == ""
    assert line.pickle.rinsing() is False
    assert line.exit.exhaust_ok() is False

    report = line.resume_cycle(PAYLOAD)
    assert report.stage == 7
    assert line.phase.value == "idle"
    assert line.strip.stopped() is True
    assert line.pump.running() is False
    assert line.strip.tail_dirty() is False
    assert line.store.exists(KEY_CYCLE) is False


def test_lost_heat_premise_scraps_a_final_stage_resume(line: Line) -> None:
    _reach(line, 7)
    _seed_checkpoint(line, stage=7, seams=2)

    # The dryer cooled while the line waited; the tail must not be stopped.
    line.dry.data.machine.force("idle")

    with pytest.raises(LineError) as raised:
        line.resume_cycle(PAYLOAD)
    assert raised.value.code is LineErrorCode.PRECONDITION_LOST
    assert "dryer-heating" in raised.value.detail
    assert line.store.exists(KEY_CYCLE) is False


def test_resume_before_the_coil_change_still_requires_the_coil(line: Line) -> None:
    _reach(line, 6)
    _seed_checkpoint(line, stage=6, seams=2)

    # The follow-up seam's track was lost during the interruption.
    line.strip.data.seam_id = ""

    with pytest.raises(LineError) as raised:
        line.resume_cycle(PAYLOAD)
    assert raised.value.code is LineErrorCode.PRECONDITION_LOST
    assert "refresh-seam-track" in raised.value.detail


def test_checkpoint_survives_a_process_restart(tmp_path: Path) -> None:
    first = Line(tmp_path)
    first.recover()

    seen = {"stage": None}
    original = first.entry.load_coil

    def fail_load(coil_id: str, target: float) -> None:
        seen["stage"] = _checkpoint(first)["stage"]
        raise RuntimeError("power loss")

    first.entry.load_coil = fail_load  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        first.production_cycle(PAYLOAD)
    first.entry.load_coil = original  # type: ignore[method-assign]
    assert seen["stage"] == 0

    second = Line(tmp_path)
    second.recover()
    checkpoint, found = second.load_checkpoint()
    assert found is True
    assert checkpoint.coil_id == PAYLOAD.coil_id

    second.resume_cycle(PAYLOAD)
    assert second.phase.value == "idle"
    assert len(second.weld_seams(0)) == 2
    assert second.strip.stopped() is True
    assert second.pump.running() is False
    assert second.store.exists(KEY_CYCLE) is False
