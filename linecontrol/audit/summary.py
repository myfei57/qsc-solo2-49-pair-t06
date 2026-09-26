"""Event counts by kind."""

from __future__ import annotations


class SummaryOps:
    """Mixed into :class:`~linecontrol.audit.logger.Logger`."""

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.state.events:
            key = event.kind.value
            counts[key] = counts.get(key, 0) + 1
        return counts
