"""Accumulated pump run hours."""

from __future__ import annotations

from datetime import datetime

from ..store.keys import KEY_HOURS
from ..store.snapshot import load_float, save_float


class RunHourOps:
    """Mixed into :class:`~linecontrol.pump.pump.Pump`."""

    def started_at(self) -> datetime | None:
        return self.data.started_at

    def record_run(self, seconds: float) -> None:
        self.data.run_seconds += max(float(seconds), 0.0)
        save_float(self.store, KEY_HOURS, self.data.run_seconds)

    def run_seconds(self) -> float:
        return self.data.run_seconds

    def restore_run(self, seconds: float) -> None:
        self.data.run_seconds = float(seconds)

    def persisted_hours(self) -> float:
        return load_float(self.store, KEY_HOURS)
