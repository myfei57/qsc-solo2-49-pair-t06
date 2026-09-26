"""Squeeze roll lift and lower, gated on the rinse valve."""

from __future__ import annotations

from .errors import ExitError, ExitErrorCode


class RollOps:
    """Mixed into :class:`~linecontrol.exit.section.Exit`."""

    def squeeze_roll_lift(self) -> None:
        """Raise the rolls only after the rinse valve has closed."""

        if self.tank.rinsing():
            raise ExitError(ExitErrorCode.RINSE_ACTIVE, "rinse still active")
        self.data.roll_up = True

    def squeeze_roll_down(self) -> None:
        self.data.roll_up = False

    def recover_lift(self) -> None:
        """Recovery path: re-check the rinse state before raising the rolls."""

        if self.tank.rinsing():
            raise ExitError(ExitErrorCode.RINSE_ACTIVE, "rinse still active")
        self.data.roll_up = True

    def roll_up(self) -> bool:
        return self.data.roll_up
