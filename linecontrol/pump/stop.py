"""Pump stop gate and stop handling."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import utcnow
from .errors import PumpError, PumpErrorCode


class StopOps:
    """Mixed into :class:`~linecontrol.pump.pump.Pump`."""

    def stop_gate(self) -> None:
        """The pump may only stop once the strip has come to rest."""

        if not self.strip_stopped():
            raise PumpError(PumpErrorCode.STRIP_RUN, "strip still running")

    def stop(self) -> None:
        self.stop_gate()
        if self.data.started_at is not None:
            elapsed = (utcnow() - self.data.started_at).total_seconds()
            self.record_run(max(elapsed, 0.0))
        self.data.started_at = None
        self.data.machine.enter("stopped")
        self._save_state()
        self.bus.publish(Event(kind=EventKind.PUMP, source="pump", message="stopped"))
