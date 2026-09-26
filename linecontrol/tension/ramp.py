"""Speed ramp planning and step application."""

from __future__ import annotations

from .errors import TensionError, TensionErrorCode
from .state import (
    DEFAULT_RAMP_STEPS,
    LONG_RAMP_STEPS,
    LONG_RAMP_TARGET,
    RampPlan,
    SpeedState,
    SpeedStep,
)

#: A step at or beyond this index is considered the final ramp step.
FINAL_STEP_INDEX = 5


class RampOps:
    """Mixed into :class:`~linecontrol.tension.roller.Roller`."""

    def plan_speedup(self, target: float) -> RampPlan:
        if target <= 0:
            raise TensionError(TensionErrorCode.INVALID_SPEED, "target speed must be positive")
        snapshot, ok = self.persisted_tension()
        if not ok or not self.data.persisted:
            raise TensionError(TensionErrorCode.RAMP_UNREADY, "tension not ready for ramp")
        count = LONG_RAMP_STEPS if target > LONG_RAMP_TARGET else DEFAULT_RAMP_STEPS
        step_size = target / count
        steps = tuple(
            SpeedStep(
                speed=step_size * index,
                setpoint=snapshot.value,
                step_index=index,
            )
            for index in range(1, count + 1)
        )
        self.data.machine.enter(SpeedState.RAMPING)
        return RampPlan(steps=steps, target=target)

    def apply_step(self, step: SpeedStep) -> None:
        if not self.data.persisted:
            raise TensionError(TensionErrorCode.RAMP_UNREADY, "tension not ready for ramp")
        self.data.setpoint = step.setpoint
        if step.step_index >= FINAL_STEP_INDEX or step.speed >= self.data.effective_tension():
            self.data.machine.enter(SpeedState.FULL)
        else:
            self.data.machine.enter(SpeedState.RUNNING)
