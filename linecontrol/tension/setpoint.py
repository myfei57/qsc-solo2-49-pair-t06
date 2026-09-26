"""Tension setpoint handling."""

from __future__ import annotations


class SetpointOps:
    """Mixed into :class:`~linecontrol.tension.roller.Roller`."""

    def apply_setpoint(self, value: float) -> None:
        self.data.setpoint = float(value)

    def setpoint(self) -> float:
        return self.data.setpoint

    def speed(self) -> str:
        return self.data.machine.state
