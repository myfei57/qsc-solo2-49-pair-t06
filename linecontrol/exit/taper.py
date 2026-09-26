"""Taper setpoint and coil weight estimation."""

from __future__ import annotations

from .state import STRIP_DENSITY, TAPER_REFERENCE_DIAMETER


class TaperOps:
    """Mixed into :class:`~linecontrol.exit.section.Exit`."""

    def taper_setpoint(self, base: float, diameter: float) -> float:
        if diameter <= 0:
            return base
        self.data.taper = base * (
            0.6 + 0.4 * diameter / TAPER_REFERENCE_DIAMETER
        )
        return self.data.taper

    def taper(self) -> float:
        return self.data.taper

    def coil_weight(
        self,
        entry_thick: float,
        exit_thick: float,
        width: float,
        length: float,
    ) -> float:
        """Coil weight from mean gauge, width and run length."""

        area = (entry_thick + exit_thick) / 2.0 * width
        return area * length * STRIP_DENSITY
