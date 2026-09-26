"""Strip stop and run flags."""

from __future__ import annotations


class StopOps:
    """Mixed into :class:`~linecontrol.strip.strip.Strip`."""

    def stop(self) -> None:
        self.data.running = False
        self.data.tail_dirty = True

    def stopped(self) -> bool:
        return not self.data.running

    def running(self) -> bool:
        return self.data.running

    def restart(self) -> None:
        self.data.running = True
