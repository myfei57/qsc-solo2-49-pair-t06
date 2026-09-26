"""Centring error and bounded correction."""

from __future__ import annotations

#: Maximum correction distance applied in a single centring step.
MAX_CORRECTION = 2.0


class CenteringOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def align_offset(self, offset: float) -> None:
        self.state.target += float(offset)

    def center_error(self) -> float:
        return self.state.target - self.state.head_pos

    def correction(self) -> float:
        delta = self.center_error()
        if delta > MAX_CORRECTION:
            return MAX_CORRECTION
        if delta < -MAX_CORRECTION:
            return -MAX_CORRECTION
        return delta
