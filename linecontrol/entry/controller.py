"""Entry controller wiring the concern-specific mixins together."""

from __future__ import annotations

from collections.abc import Callable

from ..bus import EventBus
from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.records import Confirm
from .align import AlignOps
from .centering import CenteringOps
from .coil import CoilOps
from .head import HeadOps
from .release import ReleaseOps
from .sample import SampleOps
from .state import EntryState


class Controller(CoilOps, AlignOps, CenteringOps, HeadOps, SampleOps, ReleaseOps):
    """Owns the strip head state for the entry section.

    The controller reacts to alarm and latch events on the process bus so that
    a splice release refuses to move while an overcurrent trip is standing.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._state = EntryState()
        self._interlock: Callable[[], bool] = lambda: True
        bus.subscribe(EventKind.ALARM, self._on_alarm)
        bus.subscribe(EventKind.LATCH, self._on_latch)

    @property
    def state(self) -> EntryState:
        return self._state

    @property
    def bus(self) -> EventBus:
        return self._bus

    def _on_alarm(self, event: Event) -> None:
        self._state.alarm_seen = True

    def _on_latch(self, event: Event) -> None:
        self._state.alarm_seen = False

    def alarm_seen(self) -> bool:
        return self._state.alarm_seen

    def confirm(self) -> Confirm:
        """Current alignment confirmation, refreshed lazily when pending."""

        return self._state.confirm

    def snapshot(self) -> dict[str, object]:
        """Read-only view consumed by the line state endpoint."""

        return {
            "coil": self._state.coil_id,
            "target": self._state.target,
            "head": self.head_position(),
            "aligned": self.confirm().ok,
            "position": self.confirm().position,
            "centerError": self.center_error(),
            "correction": self.correction(),
            "sampleCount": self.sample_count(),
            "sampleAvg": self.moving_average(),
            "sampleSettle": self.sample_settle(),
            "alarmSeen": self.alarm_seen(),
        }
