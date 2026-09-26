"""Alarm register kept beside the event log."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind


class AlarmOps:
    """Mixed into :class:`~linecontrol.audit.logger.Logger`."""

    def raise_alarm(self, alarm_id: str) -> None:
        self.state.alarms[alarm_id] = True
        self.bus.publish(
            Event(kind=EventKind.AUDIT, source="audit", message=f"raise:{alarm_id}")
        )

    def clear_alarm(self, alarm_id: str) -> bool:
        existed = self.state.alarms.pop(alarm_id, False)
        self.bus.publish(
            Event(kind=EventKind.AUDIT, source="audit", message=f"clear:{alarm_id}")
        )
        return existed

    def active_alarms(self) -> list[str]:
        return sorted(alarm_id for alarm_id, active in self.state.alarms.items() if active)

    def alarm_active(self, alarm_id: str) -> bool:
        return bool(self.state.alarms.get(alarm_id))
