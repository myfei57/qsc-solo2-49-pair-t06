"""Single-step operator commands forwarded to the equipment areas."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import TensionSnapshot, WeldRecord
from ..pickle.dosing import DosePlan
from ..pump.errors import PumpError, PumpErrorCode
from ..tension.state import RampPlan

#: Alarm identifier raised for a welder overcurrent trip.
WELD_OVER_CURRENT = "weld-overcurrent"


class CommandOps:
    """Mixed into :class:`~linecontrol.line.machine.Line`."""

    def recalibrate_tension(self, gain: float) -> bool:
        return self.tension.recalibrate(gain)

    def alarm_overcurrent(self) -> None:
        self.weld.alarm()
        self.last_backup = self.store.backup()
        self.audit.raise_alarm(WELD_OVER_CURRENT)

    def clear_weld_alarm(self) -> bool:
        self.weld.alarm_clear()
        return self.audit.clear_alarm(WELD_OVER_CURRENT)

    def splice_release(self) -> None:
        self.entry.splice_release()

    def track_head(self, delta: float) -> None:
        self.entry.track_head(delta)

    def align_offset(self, offset: float) -> None:
        self.entry.align_offset(offset)

    def correct_head(self) -> float:
        return self.entry.correct_head()

    def push_head_sample(self, value: float) -> None:
        self.entry.push_sample(value)

    def ramp_speed(self, target: float) -> RampPlan:
        plan = self.tension.plan_speedup(target)
        for step in plan.steps:
            self.tension.apply_step(step)
        return plan

    def replenish_acid(self, volume: float, target: float) -> DosePlan:
        plan = self.pickle.plan_dose(volume, target)
        if not plan.required:
            raise PumpError(
                PumpErrorCode.NO_REPLENISH,
                "concentration already at target",
            )
        self.pump.replenish_gate(target)
        self.pickle.apply_dose(plan.dose, volume)
        return plan

    def resume_acid_loop(self, sample: float) -> None:
        self.pickle.level_check(sample)
        self.pump.resume()

    def calibrate_acid(self, offset: float) -> None:
        self.pickle.calibrate(offset)

    def set_dryer_dew(self, dew: float) -> None:
        self.dry.set_dew_point(dew)

    def set_dryer_heat(self, target: float) -> float:
        next_temp = self.dry.heat_profile(target)
        self.dry.apply_profile(next_temp)
        return next_temp

    def reheat_dryer(self) -> None:
        self.dry.reheat()

    def set_weld_power(self, voltage: float, current: float) -> None:
        self.weld.set_power(voltage, current)

    def set_strip_speed(self, speed: float) -> None:
        self.strip.set_speed(speed)

    def advance_strip(self, delta: float) -> float:
        return self.strip.advance(delta)

    def set_shear_offset(self, offset: float) -> None:
        self.exit.set_shear_offset(offset)

    def taper_exit(self, base: float, diameter: float) -> float:
        return self.exit.taper_setpoint(base, diameter)

    def coil_weight(
        self,
        entry_thick: float,
        exit_thick: float,
        width: float,
        length: float,
    ) -> float:
        return self.exit.coil_weight(entry_thick, exit_thick, width, length)

    def sag(self) -> float:
        return self.strip.sag_check()

    def track_eta(self, target: float) -> float:
        return self.strip.eta(target)

    def persisted_tension(self) -> tuple[TensionSnapshot, bool]:
        return self.tension.persisted_tension()

    def weld_seams(self, limit: int = 0) -> list[WeldRecord]:
        return self.weld.seam_history(limit)

    def audit_query(self, kind: EventKind | None, limit: int = 0) -> list[Event]:
        if kind is None:
            return self.audit.recent(limit)
        return self.audit.query(kind, limit)
