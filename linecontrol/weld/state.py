"""Welder state and its legal transitions."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.machine import StateMachine
from ..domain.records import Confirm


class WeldState:
    """Named states of the weld cycle."""

    IDLE = "idle"
    GATED = "gated"
    WELDING = "welding"
    SPLICED = "spliced"
    FAULT = "fault"


#: Legal weld-cycle transitions, keyed by source state.
WELD_TRANSITIONS: dict[str, set[str]] = {
    WeldState.IDLE: {WeldState.GATED},
    WeldState.GATED: {WeldState.WELDING, WeldState.IDLE, WeldState.FAULT},
    WeldState.WELDING: {WeldState.SPLICED, WeldState.FAULT},
    WeldState.SPLICED: {WeldState.GATED, WeldState.FAULT},
    WeldState.FAULT: {WeldState.IDLE},
}


def new_weld_machine() -> StateMachine:
    return StateMachine("weld", WeldState.IDLE, WELD_TRANSITIONS)


@dataclass(slots=True)
class WeldStateData:
    """Mutable values carried alongside the weld-cycle machine."""

    gate: Confirm = field(default_factory=Confirm)
    track: float = 0.0
    seam_id: str = ""
    tension: float = 0.0
    latch: bool = False
    alarm: bool = False
    voltage: float = 0.0
    current: float = 0.0
    line_speed: float = 0.0
