"""Tension roller state, ramp plan and speed machine."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.machine import StateMachine

#: Recalibration smaller than this is treated as sensor noise.
GAIN_TOLERANCE = 0.05

#: Speed fractions applied by the ramp plan.
DEFAULT_RAMP_STEPS = 3
LONG_RAMP_STEPS = 5
LONG_RAMP_TARGET = 2.0


class SpeedState:
    STANDBY = "standby"
    PERMITTED = "permitted"
    RAMPING = "ramping"
    RUNNING = "running"
    FULL = "full"


SPEED_TRANSITIONS: dict[str, set[str]] = {
    SpeedState.STANDBY: {SpeedState.PERMITTED},
    SpeedState.PERMITTED: {SpeedState.RAMPING, SpeedState.RUNNING, SpeedState.STANDBY},
    SpeedState.RAMPING: {SpeedState.RUNNING, SpeedState.FULL, SpeedState.STANDBY},
    SpeedState.RUNNING: {SpeedState.RAMPING, SpeedState.FULL, SpeedState.STANDBY},
    SpeedState.FULL: {SpeedState.RAMPING, SpeedState.STANDBY},
}


def new_speed_machine() -> StateMachine:
    return StateMachine("tension-speed", SpeedState.STANDBY, SPEED_TRANSITIONS)


@dataclass(frozen=True, slots=True)
class SpeedStep:
    speed: float
    setpoint: float
    step_index: int

    def to_dict(self) -> dict[str, float]:
        return {
            "speed": self.speed,
            "setpoint": self.setpoint,
            "stepIndex": float(self.step_index),
        }


@dataclass(frozen=True, slots=True)
class RampPlan:
    steps: tuple[SpeedStep, ...]
    target: float

    def to_dict(self) -> dict[str, object]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "target": self.target,
        }


@dataclass(slots=True)
class TensionState:
    setpoint: float = 0.0
    gain: float = 1.0
    persisted: bool = False
    machine: StateMachine = field(default_factory=new_speed_machine)

    def effective_tension(self) -> float:
        """Tension actually applied to the strip after gain correction."""

        return self.setpoint * self.gain
