"""Aggregate snapshot read performed once during start-up recovery."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.records import (
    AcidSnapshot,
    LatchSnapshot,
    PumpSnapshot,
    RinseSnapshot,
    TensionSnapshot,
    TrackSnapshot,
    WeldRecord,
)
from .filestore import FileStore
from .keys import (
    KEY_ACID,
    KEY_GAIN,
    KEY_HOURS,
    KEY_LATCH,
    KEY_PUMP,
    KEY_RINSE,
    KEY_TENSION,
    KEY_TRACK,
    KEY_WELD,
)
from .snapshot import load_float, load_json


@dataclass(slots=True)
class Recovery:
    """Everything the controllers need in order to rebuild their state."""

    tension: TensionSnapshot = field(default_factory=TensionSnapshot)
    gain: float = 0.0
    acid: AcidSnapshot = field(default_factory=AcidSnapshot)
    pump: PumpSnapshot = field(default_factory=PumpSnapshot)
    track: TrackSnapshot = field(default_factory=TrackSnapshot)
    rinse: RinseSnapshot = field(default_factory=RinseSnapshot)
    latch: LatchSnapshot = field(default_factory=LatchSnapshot)
    weld: WeldRecord = field(default_factory=WeldRecord)
    run_seconds: float = 0.0
    loaded: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "tension": self.tension.to_dict(),
            "gain": self.gain,
            "acid": self.acid.to_dict(),
            "pump": self.pump.to_dict(),
            "track": self.track.to_dict(),
            "rinse": self.rinse.to_dict(),
            "latch": self.latch.to_dict(),
            "weld": self.weld.to_dict(),
            "runSeconds": self.run_seconds,
            "loaded": list(self.loaded),
        }


def collect(store: FileStore) -> Recovery:
    """Read every snapshot that exists, recording which keys were present."""

    recovery = Recovery()
    present: list[str] = []

    recovery.tension, ok = load_json(store, KEY_TENSION, TensionSnapshot)
    if ok:
        present.append(KEY_TENSION)
    recovery.gain = load_float(store, KEY_GAIN)
    if store.exists(KEY_GAIN):
        present.append(KEY_GAIN)
    recovery.acid, ok = load_json(store, KEY_ACID, AcidSnapshot)
    if ok:
        present.append(KEY_ACID)
    recovery.pump, ok = load_json(store, KEY_PUMP, PumpSnapshot)
    if ok:
        present.append(KEY_PUMP)
    recovery.track, ok = load_json(store, KEY_TRACK, TrackSnapshot)
    if ok:
        present.append(KEY_TRACK)
    recovery.rinse, ok = load_json(store, KEY_RINSE, RinseSnapshot)
    if ok:
        present.append(KEY_RINSE)
    recovery.latch, ok = load_json(store, KEY_LATCH, LatchSnapshot)
    if ok:
        present.append(KEY_LATCH)
    recovery.weld, ok = load_json(store, KEY_WELD, WeldRecord)
    if ok:
        present.append(KEY_WELD)
    recovery.run_seconds = load_float(store, KEY_HOURS)
    if store.exists(KEY_HOURS):
        present.append(KEY_HOURS)
    recovery.loaded = tuple(present)
    return recovery
