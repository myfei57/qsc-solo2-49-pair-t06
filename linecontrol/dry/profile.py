"""Dew point guard and heat profile stepping."""

from __future__ import annotations

from .errors import DryerError, DryerErrorCode
from .state import (
    MAX_DEW_POINT,
    MAX_TARGET_TEMP,
    MIN_TARGET_TEMP,
    PROFILE_RAMP,
)


class ProfileOps:
    """Mixed into :class:`~linecontrol.dry.dryer.Dryer`."""

    def set_dew_point(self, dew: float) -> None:
        self.data.dew = float(dew)

    def dew_point(self) -> float:
        return self.data.dew

    def dew_guard(self) -> None:
        if self.data.dew > MAX_DEW_POINT:
            raise DryerError(
                DryerErrorCode.DEW_HIGH,
                f"dew point {self.data.dew:.1f} above {MAX_DEW_POINT:.1f}",
            )

    def heat_profile(self, target: float) -> float:
        """Next chamber temperature towards ``target`` for one ramp step."""

        self.dew_guard()
        if target < MIN_TARGET_TEMP or target > MAX_TARGET_TEMP:
            raise DryerError(
                DryerErrorCode.TEMP_RANGE,
                f"target {target} outside {MIN_TARGET_TEMP}-{MAX_TARGET_TEMP}",
            )
        return min(target, self.data.temp + PROFILE_RAMP)

    def apply_profile(self, next_temp: float) -> None:
        self.data.temp = float(next_temp)
        self.data.machine.enter("heating")
