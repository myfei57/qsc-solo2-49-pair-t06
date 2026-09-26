"""Sag estimate driven by the current tension gain."""

from __future__ import annotations

from .state import SAG_PER_GAIN_POINT


class SagOps:
    """Mixed into :class:`~linecontrol.strip.strip.Strip`."""

    def sag_check(self) -> float:
        """Millimetres of sag implied by the live tension gain."""

        return (self.gain() - 1.0) * SAG_PER_GAIN_POINT
