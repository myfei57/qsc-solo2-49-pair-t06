"""Gain calibration for the tension roller."""

from __future__ import annotations

from ..store.keys import KEY_GAIN
from ..store.snapshot import save_float
from .errors import TensionError, TensionErrorCode
from .state import GAIN_TOLERANCE


class GainOps:
    """Mixed into :class:`~linecontrol.tension.roller.Roller`."""

    def recalibrate(self, gain: float) -> bool:
        """Apply a new gain; returns whether the stored baseline changed."""

        if gain <= 0:
            raise TensionError(TensionErrorCode.INVALID_GAIN, "gain must be positive")
        if abs(gain - self.data.gain) < GAIN_TOLERANCE:
            return False
        self.data.gain = float(gain)
        save_float(self.store, KEY_GAIN, self.data.gain)
        return True

    def gain(self) -> float:
        return self.data.gain
