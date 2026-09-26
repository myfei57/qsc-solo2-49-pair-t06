"""Mutable state owned by the entry controller."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.records import Confirm

#: Length of the moving window applied to head position samples.
SAMPLE_WINDOW = 12

#: Samples required before the settle average is considered usable.
SETTLE_MIN_SAMPLES = 3


@dataclass(slots=True)
class EntryState:
    coil_id: str = ""
    target: float = 0.0
    confirm: Confirm = field(default_factory=Confirm)
    head_pos: float = 0.0
    samples: list[float] = field(default_factory=list)
    alarm_seen: bool = False

    def reset_for_coil(self, coil_id: str, target: float) -> None:
        self.coil_id = coil_id
        self.target = target
        self.confirm = Confirm()
        self.head_pos = 0.0

    def clear_coil(self) -> None:
        self.coil_id = ""
        self.confirm = Confirm()
        self.head_pos = 0.0
