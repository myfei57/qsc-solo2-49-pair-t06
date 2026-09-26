"""Mutable state owned by the pickling tank."""

from __future__ import annotations

from dataclasses import dataclass, field

#: Minimum level, in metres, at which the circulation pump may run.
MIN_LEVEL = 2.5

#: Length of the level trend window.
TREND_WINDOW = 8


@dataclass(slots=True)
class TankState:
    level: float = 0.0
    offset: float = 0.0
    valve_open: bool = False
    flushed: bool = False
    trend: list[float] = field(default_factory=list)

    def push_level(self, value: float) -> None:
        self.trend.append(value)
        if len(self.trend) > TREND_WINDOW:
            del self.trend[: len(self.trend) - TREND_WINDOW]

    def trend_delta(self) -> float:
        """Difference between the newer and older halves of the window."""

        if len(self.trend) < 2:
            return 0.0
        half = len(self.trend) // 2
        older = self.trend[:half]
        recent = self.trend[half:]
        return _average(recent) - _average(older)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
