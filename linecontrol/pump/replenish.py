"""Replenishment gate driven by the calibrated concentration."""

from __future__ import annotations

from .errors import PumpError, PumpErrorCode


class ReplenishOps:
    """Mixed into :class:`~linecontrol.pump.pump.Pump`."""

    def replenish_gate(self, min_concentration: float) -> None:
        """Refuse a dose request while the tank is already above target."""

        concentration = self.tank.concentration()
        if concentration >= min_concentration:
            raise PumpError(
                PumpErrorCode.NO_REPLENISH,
                f"concentration {concentration:.3f} above target {min_concentration:.3f}",
            )
