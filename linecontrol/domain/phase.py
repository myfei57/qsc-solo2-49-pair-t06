"""Operating phases reported by the line controller."""

from enum import Enum


class Phase(str, Enum):
    """Coarse line phase used by the console and by the recovery logic."""

    IDLE = "idle"
    ALIGNING = "aligning"
    WELDING = "welding"
    ACID_LOOP = "acid-loop"
    DRY_HEAT = "dry-heat"
    COIL_DONE = "coil-done"
    STOPPING = "stopping"
    RECOVERING = "recovering"
    FAULT = "fault"

    def __str__(self) -> str:  # pragma: no cover - trivial formatting helper
        return self.value
