"""Strip speed, travel and arrival estimate."""

from __future__ import annotations

from .errors import StripError, StripErrorCode


class SpeedOps:
    """Mixed into :class:`~linecontrol.strip.strip.Strip`."""

    def set_speed(self, speed: float) -> None:
        if speed < 0:
            raise StripError(StripErrorCode.NO_SPEED, "strip speed must not be negative")
        self.data.speed = float(speed)

    def speed(self) -> float:
        return self.data.speed

    def advance(self, delta: float) -> float:
        self.data.travel += float(delta)
        self.data.track += float(delta)
        return self.data.track

    def travel(self) -> float:
        return self.data.travel

    def eta(self, target: float) -> float:
        """Whole seconds until the seam reaches ``target``."""

        remaining = target - self.data.track
        if remaining <= 0 or self.data.speed <= 0:
            return 0.0
        return float(round(remaining / self.data.speed))
