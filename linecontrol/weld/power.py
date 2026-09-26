"""Weld power settings and heat input."""

from __future__ import annotations

from .errors import WeldError, WeldErrorCode


class PowerOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def set_power(self, voltage: float, current: float) -> None:
        if voltage <= 0 or current <= 0:
            raise WeldError(WeldErrorCode.POWER_INVALID, "weld power invalid")
        self.data.voltage = float(voltage)
        self.data.current = float(current)

    def set_line_speed(self, speed: float) -> None:
        self.data.line_speed = float(speed)

    def heat_input(self) -> float:
        if self.data.line_speed <= 0:
            return 0.0
        return self.data.voltage * self.data.current / self.data.line_speed

    def power_state(self) -> tuple[float, float]:
        return self.data.voltage, self.data.current
