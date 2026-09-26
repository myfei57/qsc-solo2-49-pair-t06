"""Mutable strip tracking state."""

from __future__ import annotations

from dataclasses import dataclass

#: Gain deviation, per unit, mapped onto sag in millimetres.
SAG_PER_GAIN_POINT = 10.0


@dataclass(slots=True)
class StripState:
    track: float = 0.0
    seam_id: str = ""
    running: bool = True
    tail_dirty: bool = True
    speed: float = 0.0
    travel: float = 0.0
