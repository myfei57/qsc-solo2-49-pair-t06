"""Heat session bookkeeping."""

from __future__ import annotations

from ..domain.records import utcnow


class SessionOps:
    """Mixed into :class:`~linecontrol.dry.dryer.Dryer`."""

    def begin_heat(self) -> None:
        self.data.machine.enter("heating")
        self.data.started_at = utcnow()
        self.data.heat_cycles += 1

    def session_seconds(self) -> float:
        if self.data.started_at is None:
            return 0.0
        return max((utcnow() - self.data.started_at).total_seconds(), 0.0)

    def heat_cycles(self) -> int:
        return self.data.heat_cycles
