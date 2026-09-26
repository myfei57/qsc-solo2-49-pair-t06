"""Moving-window statistics over head position samples."""

from __future__ import annotations

from .state import SAMPLE_WINDOW, SETTLE_MIN_SAMPLES


class SampleOps:
    """Mixed into :class:`~linecontrol.entry.controller.Controller`."""

    def push_sample(self, value: float) -> None:
        samples = self.state.samples
        samples.append(float(value))
        if len(samples) > SAMPLE_WINDOW:
            del samples[: len(samples) - SAMPLE_WINDOW]

    def sample_count(self) -> int:
        return len(self.state.samples)

    def moving_average(self) -> float:
        samples = self.state.samples
        if not samples:
            return 0.0
        return sum(samples) / len(samples)

    def sample_settle(self) -> float:
        if len(self.state.samples) < SETTLE_MIN_SAMPLES:
            return 0.0
        return self.moving_average()
