"""Pump start gate and start/resume paths."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import utcnow
from .errors import PumpError, PumpErrorCode


class StartOps:
    """Mixed into :class:`~linecontrol.pump.pump.Pump`."""

    def start_gate(self) -> None:
        """Refuse to start unless the tank level has just been confirmed."""

        if not self.tank.level_ok():
            raise PumpError(
                PumpErrorCode.LEVEL_LOW,
                f"tank level {self.tank.level():.2f} below minimum",
            )

    def start(self) -> None:
        self.start_gate()
        self._begin_run("started")

    def resume(self) -> None:
        """Recovery path: re-evaluate the level before resuming circulation."""

        self.start_gate()
        self._begin_run("resumed")

    def _begin_run(self, message: str) -> None:
        self.data.machine.enter("running")
        self.data.started_at = utcnow()
        self._save_state()
        self.bus.publish(Event(kind=EventKind.PUMP, source="pump", message=message))
