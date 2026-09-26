"""Tension roller: setpoint, gain calibration, persist gate and speed ramp."""

from .errors import TensionError, TensionErrorCode
from .roller import Roller
from .state import RampPlan, SpeedStep, TensionState, new_speed_machine

__all__ = [
    "RampPlan",
    "Roller",
    "SpeedStep",
    "TensionError",
    "TensionErrorCode",
    "TensionState",
    "new_speed_machine",
]
