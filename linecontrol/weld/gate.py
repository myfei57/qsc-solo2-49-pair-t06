"""Arc gate: the confirmation read that authorises striking an arc."""

from __future__ import annotations

from .errors import WeldError, WeldErrorCode


class GateOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def gate_arc(self) -> None:
        confirm = self._align()
        if not confirm.ok:
            raise WeldError(WeldErrorCode.ALIGN_PENDING, "alignment not confirmed")
        self.data.gate = confirm
        self.machine.enter("gated")
