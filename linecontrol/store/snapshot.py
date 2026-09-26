"""Typed helpers layered on top of the raw file store."""

from __future__ import annotations

import json
from typing import TypeVar

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

T = TypeVar("T")

#: Record classes that can be round-tripped through the snapshot helpers.
SNAPSHOT_TYPES = (
    AcidSnapshot,
    LatchSnapshot,
    PumpSnapshot,
    RinseSnapshot,
    TensionSnapshot,
    TrackSnapshot,
    WeldRecord,
)


def save_json(store: FileStore, key: str, value: object) -> None:
    if not isinstance(value, SNAPSHOT_TYPES):
        raise TypeError(f"{type(value).__name__} is not a snapshot record")
    payload = json.dumps(value.to_dict(), ensure_ascii=False).encode("utf-8")
    store.save(key, payload)


def load_json(store: FileStore, key: str, factory: type[T]) -> tuple[T, bool]:
    raw = store.load(key)
    if raw is None or not raw.strip():
        return factory(), False
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return factory(), False
    return factory.from_dict(decoded), True


def load_float(store: FileStore, key: str) -> float:
    raw = store.load(key)
    if raw is None or not raw.strip():
        return 0.0
    try:
        return float(json.loads(raw.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return 0.0


def save_float(store: FileStore, key: str, value: float) -> None:
    store.save(key, json.dumps(float(value)).encode("utf-8"))


def save_events(store: FileStore, key: str, events: list[dict]) -> None:
    store.save(key, json.dumps(events, ensure_ascii=False).encode("utf-8"))


def load_events(store: FileStore, key: str) -> list[dict]:
    raw = store.load(key)
    if raw is None or not raw.strip():
        return []
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, list):
        return []
    return [item for item in decoded if isinstance(item, dict)]


def snapshot_type_names() -> tuple[str, ...]:
    """Names of the record classes the snapshot helpers accept."""

    return tuple(cls.__name__ for cls in SNAPSHOT_TYPES)
