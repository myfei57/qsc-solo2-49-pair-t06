"""Strip tracking, travel, tail rinse and sag."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.records import TrackSnapshot
from linecontrol.store.filestore import FileStore
from linecontrol.store.keys import KEY_TRACK
from linecontrol.strip.errors import StripError, StripErrorCode
from linecontrol.strip.strip import Strip


class Gain:
    def __init__(self, value: float = 1.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class Flushed:
    def __init__(self, value: bool = False) -> None:
        self.value = value

    def __call__(self) -> bool:
        return self.value


def build(tmp_path, gain: float = 1.0, flushed: bool = False):
    gain_fn = Gain(gain)
    flushed_fn = Flushed(flushed)
    strip = Strip(FileStore(tmp_path), EventBus(), gain_fn, flushed_fn)
    return strip, gain_fn, flushed_fn


def test_track_update_persists_and_gates_the_shear(tmp_path) -> None:
    strip, _, _ = build(tmp_path)
    assert strip.shear_permit() is False
    strip.track_update(64.0)
    assert strip.track_position() == pytest.approx(64.0)
    assert strip.store.exists(KEY_TRACK)
    assert strip.shear_permit() is False
    strip.track_refresh(64.0, "seam-9")
    assert strip.shear_permit() is True
    assert strip.seam_id() == "seam-9"


def test_restore_track_reads_a_snapshot(tmp_path) -> None:
    strip, _, _ = build(tmp_path)
    strip.restore_track(TrackSnapshot(position=33.0, seam_id="seam-3"))
    assert strip.track_position() == pytest.approx(33.0)
    assert strip.seam_id() == "seam-3"


def test_speed_validation_and_travel(tmp_path) -> None:
    strip, _, _ = build(tmp_path)
    with pytest.raises(StripError) as caught:
        strip.set_speed(-1.0)
    assert caught.value.code is StripErrorCode.NO_SPEED
    strip.set_speed(2.0)
    assert strip.speed() == pytest.approx(2.0)
    assert strip.advance(15.0) == pytest.approx(15.0)
    assert strip.travel() == pytest.approx(15.0)


def test_eta_uses_speed_and_remaining_distance(tmp_path) -> None:
    strip, _, _ = build(tmp_path)
    strip.track_update(10.0)
    assert strip.eta(100.0) == 0.0
    strip.set_speed(4.0)
    assert strip.eta(90.0) == pytest.approx(20.0)
    assert strip.eta(100.0) == pytest.approx(22.0)


def test_tail_rinse_requires_a_stopped_and_flushed_strip(tmp_path) -> None:
    strip, _, flushed = build(tmp_path)
    with pytest.raises(StripError) as caught:
        strip.tail_rinse()
    assert caught.value.code is StripErrorCode.STRIP_RUN
    strip.stop()
    assert strip.stopped() is True
    with pytest.raises(StripError) as caught:
        strip.tail_rinse()
    assert caught.value.code is StripErrorCode.TAIL_UNFLUSHED
    flushed.value = True
    strip.tail_rinse()
    assert strip.tail_dirty() is False
    strip.restart()
    assert strip.running() is True


def test_sag_follows_the_live_gain(tmp_path) -> None:
    strip, gain, _ = build(tmp_path)
    assert strip.sag_check() == pytest.approx(0.0)
    gain.value = 1.4
    assert strip.sag_check() == pytest.approx(4.0)


def test_snapshot_view(tmp_path) -> None:
    strip, _, _ = build(tmp_path)
    strip.track_refresh(20.0, "seam-1")
    view = strip.snapshot()
    assert view["track"] == pytest.approx(20.0)
    assert view["seam"] == "seam-1"
    assert view["tailDirty"] is True
