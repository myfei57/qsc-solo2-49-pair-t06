"""Dryer state values and transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..domain.machine import StateMachine

#: Default chamber temperature when a heat cycle begins, in degrees Celsius.
HEAT_START_TEMP = 120.0

#: Initial dew point when no measurement has been taken yet.
DEFAULT_DEW_POINT = -20.0

#: Heating is refused while the dew point is above this value.
MAX_DEW_POINT = 40.0

#: Accepted band for a requested chamber temperature.
MIN_TARGET_TEMP = 60.0
MAX_TARGET_TEMP = 180.0

#: Maximum temperature rise applied by a single profile step.
PROFILE_RAMP = 15.0


class DryerState:
    IDLE = "idle"
    HEATING = "heating"
    HOLDING = "holding"


DRYER_TRANSITIONS: dict[str, set[str]] = {
    DryerState.IDLE: {DryerState.HEATING},
    DryerState.HEATING: {DryerState.HOLDING, DryerState.IDLE},
    DryerState.HOLDING: {DryerState.HEATING, DryerState.IDLE},
}


def new_dryer_machine() -> StateMachine:
    return StateMachine("dryer", DryerState.IDLE, DRYER_TRANSITIONS)


@dataclass(slots=True)
class DryerData:
    temp: float = 0.0
    dew: float = DEFAULT_DEW_POINT
    started_at: datetime | None = None
    heat_cycles: int = 0
    machine: StateMachine = field(default_factory=new_dryer_machine)

    def heating(self) -> bool:
        return self.machine.state == DryerState.HEATING
