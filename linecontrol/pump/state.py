"""Pump run state and its transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..domain.machine import StateMachine


class PumpState:
    STOPPED = "stopped"
    RUNNING = "running"


PUMP_TRANSITIONS: dict[str, set[str]] = {
    PumpState.STOPPED: {PumpState.RUNNING},
    PumpState.RUNNING: {PumpState.STOPPED},
}


def new_pump_machine() -> StateMachine:
    return StateMachine("pump", PumpState.STOPPED, PUMP_TRANSITIONS)


@dataclass(slots=True)
class PumpData:
    started_at: datetime | None = None
    run_seconds: float = 0.0
    machine: StateMachine = field(default_factory=new_pump_machine)

    def running(self) -> bool:
        return self.machine.state == PumpState.RUNNING
