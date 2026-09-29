"""Multi-stage call chains that cross equipment areas.

The production cycle is a fixed sequence of eight stages.  After every stage
completes a :class:`~linecontrol.domain.records.CycleCheckpoint` is written to
the store.  A cycle interrupted part-way can therefore be resumed: the
checkpoint says which stage is next, and the preconditions left behind by every
earlier stage are re-verified before motion is allowed.  If one of those
premises no longer holds the partial run is scrapped and the whole cycle has to
start over.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.phase import Phase
from ..domain.records import CycleCheckpoint, utcnow
from ..store.keys import KEY_CYCLE
from ..store.snapshot import load_json, save_json
from .errors import LineError, LineErrorCode

#: Number of stages that make up one production cycle.
STAGE_COUNT = 8


@dataclass(frozen=True, slots=True)
class CycleInput:
    """Arguments for a complete production cycle."""

    coil_id: str
    target: float
    level: float
    voltage: float
    current: float
    speed: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "coil": self.coil_id,
            "target": self.target,
            "level": self.level,
            "voltage": self.voltage,
            "current": self.current,
            "speed": self.speed,
        }

    def changed_from(self, saved: "CycleInput") -> tuple[str, ...]:
        """Names of the arguments that differ from the saved ``saved`` run."""

        mismatches: list[str] = []
        if self.coil_id != saved.coil_id:
            mismatches.append("coil")
        for name in ("target", "level", "voltage", "current", "speed"):
            if getattr(self, name) != getattr(saved, name):
                mismatches.append(name)
        return tuple(mismatches)


@dataclass(frozen=True, slots=True)
class ResumeReport:
    """Outcome of a resume request."""

    resumed: bool
    stage: int
    completed: bool
    preconditions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "resumed": self.resumed,
            "stage": self.stage,
            "completed": self.completed,
            "preconditions": list(self.preconditions),
        }


class WorkflowOps:
    """Mixed into :class:`~linecontrol.line.machine.Line`."""

    def load_coil(self, coil_id: str, target: float) -> None:
        self.coil_no += 1
        self.handle = self.audit.new_handle()
        self._load_coil_stage(coil_id, target)

    def _load_coil_stage(self, coil_id: str, target: float) -> None:
        """The load step itself, without the bookkeeping kept idempotent."""

        self.entry.load_coil(coil_id, target)
        self.strip.restart()

    def weld_and_speedup(self) -> None:
        """Align, strike the arc, persist the tension, then permit speed-up.

        The speed-up call is placed after the tension has been written to the
        store so that a restart pulls the seam at the tension it was welded
        with rather than at whatever the previous seam used.
        """

        self.seq.begin_if_idle("weld-and-speedup")
        self.set_phase(Phase.ALIGNING)
        try:
            self.entry.align_confirm()
            self.seq.record("align-confirm")
            self.set_phase(Phase.WELDING)
            self.weld.gate_arc()
            self.seq.record("arc-gate")
            self.weld.arc()
            self.seq.record("arc")
            self.weld.persist_tension(self.tension.setpoint(), self.tension.gain())
            self.seq.record("tension-persist")
            self.weld.splice()
            self.seq.record("splice")
            self.tension.allow_speedup()
            self.seq.record("speedup")
            self.strip.track_update(self.weld.track_point())
            self.seq.record("track-update")
        except Exception as error:
            self.seq.record("aborted", error)
            self.set_phase(Phase.FAULT)
            raise
        self.set_phase(Phase.ACID_LOOP)

    def splice_and_refresh(self, position: float) -> None:
        """Refresh the alignment, weld a follow-up seam and move the track.

        The refresh has to land before the arc gate re-reads the confirmation,
        and the track has to move onto the new seam before the exit shear is
        allowed to cut.
        """

        try:
            self.entry.align_refresh(position)
            self.weld.set_line_speed(self.strip.speed())
            self.weld.arc_post_splice()
            self.weld.splice()
            self.strip.track_refresh(self.weld.track_point(), self.weld.seam_id())
        except Exception:
            self.set_phase(Phase.FAULT)
            raise

    def start_acid_loop(self, sample: float) -> None:
        """Confirm the level, start the pump and open the rinse valve."""

        try:
            self.pickle.level_check(sample)
            self.seq.record("level-check")
            self.pump.start_gate()
            self.seq.record("pump-gate")
            self.pump.start()
            self.seq.record("pump-start")
            self.pickle.rinse()
            self.seq.record("rinse")
            self.exit.squeeze_roll_down()
            self.seq.record("squeeze-down")
        except Exception as error:
            self.seq.record("aborted", error)
            raise

    def heat_dryer_and_coil(self) -> None:
        """Establish exhaust, heat the dryer and run a coil change."""

        try:
            self.exit.exhaust_establish()
            self.seq.record("exhaust")
            self.dry.heat_gate()
            self.seq.record("heat-gate")
            self.dry.heat()
            self.seq.record("heat")
            self.set_phase(Phase.DRY_HEAT)
            self.coil_change()
            self.seq.record("coil-change")
        except Exception as error:
            self.seq.record("aborted", error)
            raise

    def coil_change(self) -> None:
        try:
            self.exit.coil_change()
            self.entry.coil_change()
        except Exception:
            self.set_phase(Phase.FAULT)
            raise
        self.exit.data.reset_sequence()
        self.set_phase(Phase.COIL_DONE)

    def stop_line(self) -> None:
        """Stop the strip, flush the tail, then stop the pump."""

        self.set_phase(Phase.STOPPING)
        try:
            self.strip.stop()
            self.seq.record("strip-stop")
            self.pickle.rinse_flush()
            self.seq.record("rinse-flush")
            self.pump.stop_gate()
            self.seq.record("pump-gate")
            self.pump.stop()
            self.seq.record("pump-stop")
            self.strip.tail_rinse()
            self.seq.record("tail-rinse")
        except Exception as error:
            self.seq.record("aborted", error)
            self.set_phase(Phase.FAULT)
            raise
        self.exit.exhaust_reset()
        self.set_phase(Phase.IDLE)
        self.bus.publish(Event(kind=EventKind.STOP, source="line", message="stopped"))

    # -- resumable production cycle -------------------------------------

    #: Human-readable name of each stage, in execution order.
    STAGE_NAMES: tuple[str, ...] = (
        "load-coil",
        "weld-speedup",
        "acid-loop",
        "set-speed",
        "set-power",
        "splice-refresh",
        "dry-coil",
        "stop",
    )

    def _stage_runners(self, payload: CycleInput) -> tuple[Callable[[], None], ...]:
        return (
            lambda: self._load_coil_stage(payload.coil_id, payload.target),
            self.weld_and_speedup,
            lambda: self.start_acid_loop(payload.level),
            lambda: self.set_strip_speed(payload.speed),
            lambda: self.set_weld_power(payload.voltage, payload.current),
            lambda: self.splice_and_refresh(payload.target + 30),
            self.heat_dryer_and_coil,
            self.stop_line,
        )

    def _save_checkpoint(self, checkpoint: CycleCheckpoint) -> None:
        save_json(self.store, KEY_CYCLE, replace(checkpoint, saved=utcnow()))

    def load_checkpoint(self) -> tuple[CycleCheckpoint, bool]:
        return load_json(self.store, KEY_CYCLE, CycleCheckpoint)

    def _clear_checkpoint(self) -> None:
        self.store.delete(KEY_CYCLE)

    def production_cycle(self, payload: CycleInput) -> None:
        """Run load, weld, acid loop, dry and stop as one sequence.

        A checkpoint is written before the first stage moves so that an
        interruption during coil load still leaves a resumable run.  Any
        checkpoint from an earlier, scrapped cycle is removed first: starting
        a production cycle is the explicit "start over" path.
        """

        self._clear_checkpoint()
        self.coil_no += 1
        self.handle = self.audit.new_handle()
        self.seq.begin("production")
        checkpoint = CycleCheckpoint.from_input(
            payload,
            self.coil_no,
            self.handle,
            stage=0,
            seams=len(self.weld_seams(0)),
        )
        self._save_checkpoint(checkpoint)
        self._run_cycle(payload, checkpoint)

    def resume_cycle(self, payload: CycleInput) -> ResumeReport:
        """Continue an interrupted cycle from the stage after the checkpoint.

        Every premise established by the stages already completed is
        re-verified first.  When one of them is gone the checkpoint is
        discarded and :class:`LineError` is raised, so the operator must
        scrap the run and start a fresh cycle instead of half-continuing.
        """

        checkpoint, found = self.load_checkpoint()
        if not found or not checkpoint.coil_id:
            raise LineError(LineErrorCode.NO_CHECKPOINT, "no interrupted cycle to resume")
        if checkpoint.stage >= STAGE_COUNT:
            raise LineError(LineErrorCode.CYCLE_DONE, "cycle already completed")

        missing = tuple(
            f"input:{name}"
            for name in payload.changed_from(
                CycleInput(
                    coil_id=checkpoint.coil_id,
                    target=checkpoint.target,
                    level=checkpoint.level,
                    voltage=checkpoint.voltage,
                    current=checkpoint.current,
                    speed=checkpoint.speed,
                )
            )
        )
        missing += tuple(self._verify_preconditions(checkpoint))
        if missing:
            self._clear_checkpoint()
            self.set_phase(Phase.FAULT)
            raise LineError(
                LineErrorCode.PRECONDITION_LOST,
                "cycle preconditions no longer hold: " + ", ".join(missing),
            )

        self.coil_no = checkpoint.coil_no
        self.handle = checkpoint.handle
        self.seq.begin_if_idle("production")
        self.seq.record(f"resume:{self.STAGE_NAMES[checkpoint.stage]}")
        self._run_cycle(payload, checkpoint)
        return ResumeReport(
            resumed=True,
            stage=checkpoint.stage,
            completed=True,
            preconditions=(),
        )

    def _run_cycle(self, payload: CycleInput, checkpoint: CycleCheckpoint) -> None:
        runners = self._stage_runners(payload)
        stage = checkpoint.stage
        try:
            while stage < STAGE_COUNT:
                runners[stage]()
                self.seq.record(f"stage:{self.STAGE_NAMES[stage]}")
                stage += 1
                seams = len(self.weld_seams(0))
                self._save_checkpoint(replace(checkpoint, stage=stage, seams=seams))
        except Exception as error:
            self.seq.record("aborted", error)
            raise
        self._clear_checkpoint()

    # -- precondition verification --------------------------------------

    def _verify_preconditions(
        self, checkpoint: CycleCheckpoint
    ) -> tuple[str, ...]:
        """Verify the premises needed to run the next (not yet completed) stage.

        ``checkpoint.stage`` is the count of stages that already completed, so
        each check applies only to the boundaries where that premise holds.
        The stage about to (re-)run is deliberately *not* checked for its own
        result.  Some premises are transient: the loaded coil is consumed by
        the stage-6 coil change and the rinse valve closes during that same
        change, so those two are required only up to the boundary before it.
        """

        stage = checkpoint.stage
        missing: list[str] = []

        # Stage 0 (load-coil) leaves the coil on the entry until stage 6.
        if 1 <= stage < 7 and self.entry.coil_id() != checkpoint.coil_id:
            missing.append("coil-loaded")

        # Stage 1 (weld-speedup) leaves the spliced seam and the speed permit.
        if stage >= 2:
            if self.weld.state() != "spliced":
                missing.append("weld-spliced")
            if not self.tension.speed_permitted():
                missing.append("speedup-permitted")
            if self.strip.track_position() <= 0:
                missing.append("track-point")
            if len(self.weld_seams(0)) < max(checkpoint.seams, 1):
                missing.append("weld-seam-record")

        # Stage 2 (acid-loop) starts circulation; the rinse valve and the
        # lowered rolls persist until the stage-6 coil change stops the rinse
        # and lifts the rolls, hence the upper bounds at boundary 7.
        if stage >= 3:
            if not self.pickle.level_ok():
                missing.append("acid-level")
            if not self.pump.running():
                missing.append("pump-running")
        if 3 <= stage < 7:
            if not self.pickle.rinsing():
                missing.append("rinse-open")
            if self.exit.roll_up():
                missing.append("squeeze-roll-down")

        # Stage 3 (set-speed) sets the line speed used by the follow-up weld.
        if stage >= 4 and self.strip.speed() != checkpoint.speed:
            missing.append("strip-speed")

        # Stage 4 (set-power) sets the welder voltage and current.
        if stage >= 5:
            voltage, current = self.weld.power_state()
            if voltage != checkpoint.voltage or current != checkpoint.current:
                missing.append("weld-power")

        # Stage 5 (splice-refresh) moves the track onto the second seam.
        if stage >= 6:
            if self.strip.seam_id() != self.weld.seam_id() or not self.weld.seam_id():
                missing.append("refresh-seam-track")
            if len(self.weld_seams(0)) < max(checkpoint.seams, 2):
                missing.append("second-weld-seam")

        # Stage 6 (dry-coil) establishes exhaust, heats the dryer and changes
        # the coil.  ``coil_change`` then resets the exit sequence (including
        # the exhaust flag) and removes the coil from the entry, so only the
        # heated dryer still distinguishes this boundary.
        if stage >= 7 and not self.dry.data.heating():
            missing.append("dryer-heating")

        # Stage 7 (stop) is the last stage; a completed cycle deletes its
        # checkpoint, so there is no boundary beyond it to verify.
        return tuple(missing)
