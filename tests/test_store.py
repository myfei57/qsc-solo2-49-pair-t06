"""File store, snapshot helpers and recovery aggregation."""

from __future__ import annotations

import json

import pytest

from linecontrol.domain.records import (
    AcidSnapshot,
    LatchSnapshot,
    PumpSnapshot,
    RinseSnapshot,
    TensionSnapshot,
    TrackSnapshot,
    WeldRecord,
)
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import (
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
from linecontrol.store.recovery import collect
from linecontrol.store.snapshot import (
    load_float,
    load_json,
    save_float,
    save_json,
    snapshot_type_names,
)


def test_save_and_load_round_trip(tmp_path) -> None:
    store = FileStore(tmp_path)
    record = WeldRecord(seam_id="s1", position=42.0, tension=88.0, heat_input=3.0)
    save_json(store, KEY_WELD, record)
    restored, ok = load_json(store, KEY_WELD, WeldRecord)
    assert ok is True
    assert restored == record
    assert store.exists(KEY_WELD) is True
    assert store.list("weld.") == [KEY_WELD]


def test_load_json_missing_and_corrupt(tmp_path) -> None:
    store = FileStore(tmp_path)
    empty, ok = load_json(store, "missing.key", TensionSnapshot)
    assert ok is False and empty.value == 0.0
    store.save("broken.key", b"{not json")
    broken, ok = load_json(store, "broken.key", TensionSnapshot)
    assert ok is False and broken.value == 0.0


def test_save_json_rejects_a_foreign_object(tmp_path) -> None:
    store = FileStore(tmp_path)
    with pytest.raises(TypeError):
        save_json(store, "bad.key", {"value": 1})


def test_float_helpers(tmp_path) -> None:
    store = FileStore(tmp_path)
    assert load_float(store, KEY_GAIN) == 0.0
    save_float(store, KEY_GAIN, 1.15)
    assert load_float(store, KEY_GAIN) == pytest.approx(1.15)
    store.save(KEY_HOURS, b"null")
    assert load_float(store, KEY_HOURS) == 0.0


def test_store_rejects_a_path_traversal_key(tmp_path) -> None:
    store = FileStore(tmp_path)
    with pytest.raises(ValueError):
        store.save("../escape", b"x")


def test_rotate_trims_a_json_array(tmp_path) -> None:
    store = FileStore(tmp_path)
    store.save("list.key", json.dumps(list(range(10))).encode("utf-8"))
    assert store.rotate("list.key", 4) == 6
    trimmed = json.loads(store.load("list.key").decode("utf-8"))
    assert trimmed == [6, 7, 8, 9]
    assert store.rotate("list.key", 4) == 0
    assert store.rotate("absent.key", 4) == 0


def test_rotate_ignores_a_non_array(tmp_path) -> None:
    store = FileStore(tmp_path)
    store.save("obj.key", b'{"a": 1}')
    assert store.rotate("obj.key", 1) == 0


def test_backup_copies_every_snapshot(tmp_path) -> None:
    store = FileStore(tmp_path)
    save_float(store, KEY_GAIN, 1.2)
    save_json(store, KEY_PUMP, PumpSnapshot(running=True))
    summary = store.backup()
    assert summary.count == 2
    assert KEY_GAIN in summary.files
    assert summary.bytes_written > 0
    assert set(store.backup_files()) == {KEY_GAIN, KEY_PUMP}
    assert summary.to_dict()["count"] == 2


def test_backup_files_on_an_unused_store(tmp_path) -> None:
    store = FileStore(tmp_path / "fresh")
    assert store.backup_files() == ()


def test_collect_reports_only_present_snapshots(tmp_path) -> None:
    store = FileStore(tmp_path)
    save_json(store, KEY_TENSION, TensionSnapshot(value=77.0, gain=1.1))
    save_json(store, KEY_ACID, AcidSnapshot(level=5.0, offset=0.5))
    save_json(store, KEY_PUMP, PumpSnapshot(running=True))
    save_json(store, KEY_TRACK, TrackSnapshot(position=9.0, seam_id="s"))
    save_json(store, KEY_RINSE, RinseSnapshot(active=True))
    save_json(store, KEY_LATCH, LatchSnapshot(interlock=True, alarm=True))
    save_float(store, KEY_HOURS, 120.0)
    state = collect(store)
    assert state.tension.value == pytest.approx(77.0)
    assert state.acid.level == pytest.approx(5.0)
    assert state.pump.running is True
    assert state.track.seam_id == "s"
    assert state.rinse.active is True
    assert state.latch.interlock is True
    assert state.run_seconds == pytest.approx(120.0)
    assert KEY_WELD not in state.loaded
    assert state.to_dict()["gain"] == 0.0


def test_snapshot_type_names_are_listed() -> None:
    names = snapshot_type_names()
    assert "TensionSnapshot" in names
    assert "WeldRecord" in names
