"""Multi-stage call chains that cross equipment areas."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.phase import Phase


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


class WorkflowOps:
    """Mixed into :class:`~linecontrol.line.machine.Line`."""

    def load_coil(self, coil_id: str, target: float) -> None:
        self.coil_no += 1
        self.handle = self.audit.new_handle()
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

    def production_cycle(self, payload: CycleInput) -> None:
        """Run load, weld, acid loop, dry and stop as one sequence."""

        self.seq.begin("production")
        self.load_coil(payload.coil_id, payload.target)
        self.seq.record("stage:load-coil")
        self.weld_and_speedup()
        self.seq.record("stage:weld-speedup")
        self.start_acid_loop(payload.level)
        self.seq.record("stage:acid-loop")
        self.set_strip_speed(payload.speed)
        self.seq.record("stage:set-speed")
        self.set_weld_power(payload.voltage, payload.current)
        self.seq.record("stage:set-power")
        self.splice_and_refresh(payload.target + 30)
        self.seq.record("stage:splice-refresh")
        self.heat_dryer_and_coil()
        self.seq.record("stage:dry-coil")
        self.stop_line()
        self.seq.record("stage:stop")
