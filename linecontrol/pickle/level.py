"""Tank level sampling and the level gate."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from .state import MIN_LEVEL


class LevelOps:
    """Mixed into :class:`~linecontrol.pickle.tank.Tank`."""

    def level_check(self, sample: float) -> None:
        """Record a fresh level reading and publish it on the bus."""

        self.data.level = float(sample)
        self.push_level(float(sample))
        self.bus.publish(
            Event(
                kind=EventKind.LEVEL,
                source="pickle",
                message="sampled",
                payload=float(sample),
            )
        )

    def level_ok(self) -> bool:
        return self.data.level >= MIN_LEVEL

    def level(self) -> float:
        return self.data.level

    def minimum_level(self) -> float:
        return MIN_LEVEL
