"""Arc strike and post-splice arc path."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .errors import WeldError, WeldErrorCode
from .state import WeldState


class ArcOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def arc(self) -> None:
        if not self.data.gate.ok:
            raise WeldError(WeldErrorCode.ARC_BLOCKED, "arc gate closed")
        if self.data.latch:
            raise WeldError(WeldErrorCode.LATCH_HELD, "interlock latch held")
        self.machine.enter(WeldState.WELDING)
        self.data.track = self.data.gate.position
        self.bus.publish(
            Event(
                kind=EventKind.ARC,
                source="weld",
                message="arc struck",
                payload=self.data.track,
            )
        )

    def arc_post_splice(self) -> None:
        """Re-gate and strike an arc for a follow-up seam."""

        self.gate_arc()
        self.arc()
