"""Re-heat path taken after a fault is reset."""

from __future__ import annotations

from .state import HEAT_START_TEMP


class ReheatOps:
    """Mixed into :class:`~linecontrol.dry.dryer.Dryer`."""

    def reheat(self) -> None:
        """Re-establish a heat cycle; exhaust is re-checked, not assumed."""

        self.heat_gate()
        self.begin_heat()
        self.data.temp = HEAT_START_TEMP
        self.announce("reheated")
