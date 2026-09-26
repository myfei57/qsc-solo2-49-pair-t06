"""Event kinds published on the process bus."""

from enum import Enum


class EventKind(str, Enum):
    """Every published process event carries exactly one kind."""

    COIL = "coil"
    ALIGN = "align"
    ARC = "arc"
    WELD = "weld"
    TENSION = "tension"
    PUMP = "pump"
    LEVEL = "level"
    RINSE = "rinse"
    DRY = "dry"
    EXHAUST = "exhaust"
    SHEAR = "shear"
    TRACK = "track"
    LATCH = "latch"
    ALARM = "alarm"
    RECOVER = "recover"
    STOP = "stop"
    AUDIT = "audit"

    def __str__(self) -> str:  # pragma: no cover - trivial formatting helper
        return self.value


#: Kinds the console forwards to browser clients, in publication order.
STREAM_KINDS: tuple[EventKind, ...] = (
    EventKind.COIL,
    EventKind.ALIGN,
    EventKind.ARC,
    EventKind.WELD,
    EventKind.TENSION,
    EventKind.PUMP,
    EventKind.LEVEL,
    EventKind.RINSE,
    EventKind.DRY,
    EventKind.EXHAUST,
    EventKind.SHEAR,
    EventKind.TRACK,
    EventKind.LATCH,
    EventKind.ALARM,
    EventKind.RECOVER,
    EventKind.STOP,
    EventKind.AUDIT,
)
