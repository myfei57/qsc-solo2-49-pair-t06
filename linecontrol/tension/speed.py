"""Speed-up permission tied to the persisted weld tension."""

from __future__ import annotations

from ..domain.records import TensionSnapshot
from .errors import TensionError, TensionErrorCode
from .state import SpeedState


class SpeedOps:
    """Mixed into :class:`~linecontrol.tension.roller.Roller`."""

    def allow_speedup(self) -> TensionSnapshot:
        """Permit the run only once a fresh tension snapshot is on disk."""

        snapshot, ok = self.persisted_tension()
        if not ok:
            raise TensionError(
                TensionErrorCode.NOT_PERSISTED, "weld tension not persisted"
            )
        self.data.setpoint = snapshot.value
        if snapshot.gain > 0:
            self.data.gain = snapshot.gain
        self.data.persisted = True
        self.data.machine.enter(SpeedState.PERMITTED)
        self.data.machine.enter(SpeedState.RUNNING)
        return snapshot

    def speed_permitted(self) -> bool:
        return self.data.persisted
