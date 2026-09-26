"""Persisted seam history."""

from __future__ import annotations

from ..domain.records import WeldRecord
from ..store.keys import KEY_WELD, SEAM_PREFIX
from ..store.snapshot import load_json


class SeamsOps:
    """Mixed into :class:`~linecontrol.weld.welder.Welder`."""

    def seam_history(self, limit: int = 0) -> list[WeldRecord]:
        records: list[WeldRecord] = []
        for key in self.store.list(SEAM_PREFIX):
            record, ok = load_json(self.store, key, WeldRecord)
            if ok:
                records.append(record)
        records.sort(key=lambda item: item.at, reverse=True)
        if limit > 0:
            return records[:limit]
        return records

    def last_weld(self) -> tuple[WeldRecord, bool]:
        return load_json(self.store, KEY_WELD, WeldRecord)
