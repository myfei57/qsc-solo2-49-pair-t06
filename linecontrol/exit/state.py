"""Mutable state owned by the exit section."""

from __future__ import annotations

from dataclasses import dataclass

#: Roll diameter, in millimetres, above which a taper is fully developed.
TAPER_REFERENCE_DIAMETER = 100.0

#: Strip density used for coil weight, in kg per cubic millimetre.
STRIP_DENSITY = 7.85e-3


@dataclass(slots=True)
class ExitState:
    exhaust: bool = False
    roll_up: bool = False
    shear_pos: float = 0.0
    taper: float = 0.0
    shear_offset: float = 0.0

    def reset_sequence(self) -> None:
        self.exhaust = False
        self.roll_up = False
        self.shear_pos = 0.0
        self.taper = 0.0
