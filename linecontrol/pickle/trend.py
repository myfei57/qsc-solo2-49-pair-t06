"""Level trend helpers."""

from __future__ import annotations


class TrendOps:
    """Mixed into :class:`~linecontrol.pickle.tank.Tank`."""

    def push_level(self, value: float) -> None:
        self.data.push_level(float(value))

    def level_trend(self) -> float:
        return self.data.trend_delta()
