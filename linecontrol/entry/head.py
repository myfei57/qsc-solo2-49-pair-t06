"""Strip head position tracking."""

from __future__ import annotations


class HeadOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def track_head(self, delta: float) -> None:
        self.state.head_pos += float(delta)

    def head_position(self) -> float:
        return self.state.head_pos

    def correct_head(self) -> float:
        """Move the head by the bounded centring correction."""

        step = self.correction()
        self.track_head(step)
        return step
