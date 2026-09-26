"""Replenishment volume planning."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import PickleError, PickleErrorCode


@dataclass(frozen=True, slots=True)
class DosePlan:
    required: bool
    dose: float
    current: float
    target: float

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "required": self.required,
            "dose": self.dose,
            "current": self.current,
            "target": self.target,
        }


class DosingOps:
    """Mixed into :class:`~linecontrol.pickle.tank.Tank`."""

    def dose_volume(self, volume: float, target: float) -> float:
        if volume <= 0:
            raise PickleError(PickleErrorCode.TANK_VOLUME, "tank volume must be positive")
        shortfall = target - self.concentration()
        if shortfall <= 0:
            return 0.0
        return shortfall * volume

    def plan_dose(self, volume: float, target: float) -> DosePlan:
        dose = self.dose_volume(volume, target)
        return DosePlan(
            required=dose > 0,
            dose=dose,
            current=self.concentration(),
            target=float(target),
        )

    def apply_dose(self, dose: float, volume: float) -> None:
        if volume > 0:
            self.data.level += dose / volume
