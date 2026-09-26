"""Acid concentration calibration offset."""

from __future__ import annotations

from ..domain.records import AcidSnapshot, utcnow
from ..store.keys import KEY_ACID
from ..store.snapshot import save_json
from .errors import PickleError, PickleErrorCode

#: A calibration offset outside this band is treated as an instrument fault.
MAX_OFFSET = 50.0


class ConcentrationOps:
    """Mixed into :class:`~linecontrol.pickle.tank.Tank`."""

    def calibrate(self, offset: float) -> None:
        if abs(offset) > MAX_OFFSET:
            raise PickleError(
                PickleErrorCode.OFFSET_INVALID,
                f"calibration offset {offset} outside ±{MAX_OFFSET}",
            )
        self.data.offset = float(offset)
        save_json(
            self.store,
            KEY_ACID,
            AcidSnapshot(
                level=self.data.level,
                offset=self.data.offset,
                saved=utcnow(),
            ),
        )

    def offset(self) -> float:
        return self.data.offset

    def concentration(self) -> float:
        """Calibrated concentration used by the replenishment decision."""

        return self.data.level + self.data.offset

    def restore_acid(self, snapshot: AcidSnapshot) -> None:
        self.data.level = snapshot.level
        self.data.offset = snapshot.offset
