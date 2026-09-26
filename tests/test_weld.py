"""Welder gating, splicing and the interlock latch."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.domain.records import Confirm, LatchSnapshot, utcnow
from linecontrol.store.filestore import FileStore
from linecontrol.weld.errors import WeldError, WeldErrorCode
from linecontrol.weld.state import WeldState
from linecontrol.weld.welder import Welder


class Aligner:
    """Stand-in for the entry section's confirmation lookup."""

    def __init__(self) -> None:
        self.confirm = Confirm(ok=False)

    def __call__(self) -> Confirm:
        return self.confirm


def build(tmp_path) -> tuple[Welder, Aligner]:
    aligner = Aligner()
    welder = Welder(aligner, FileStore(tmp_path), EventBus())
    return welder, aligner


def test_gate_refuses_without_a_confirmation(tmp_path) -> None:
    welder, _ = build(tmp_path)
    with pytest.raises(WeldError) as caught:
        welder.gate_arc()
    assert caught.value.code is WeldErrorCode.ALIGN_PENDING
    assert welder.state() == WeldState.IDLE


def test_arc_uses_the_confirmation_read_at_gate_time(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=100.0, at=utcnow())
    welder.gate_arc()
    aligner.confirm = Confirm(ok=True, position=175.0, at=utcnow())
    welder.gate_arc()
    welder.arc()
    assert welder.track_point() == pytest.approx(175.0)
    assert welder.state() == WeldState.WELDING


def test_arc_is_blocked_while_the_latch_is_held(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=100.0, at=utcnow())
    welder.alarm()
    welder.gate_arc()
    with pytest.raises(WeldError) as caught:
        welder.arc()
    assert caught.value.code is WeldErrorCode.LATCH_HELD
    welder.alarm_clear()
    welder.gate_arc()
    welder.arc()
    assert welder.interlock_ok()


def test_splice_writes_both_the_record_and_the_seam(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=88.0, at=utcnow())
    welder.set_line_speed(1.5)
    welder.set_power(24.0, 300.0)
    welder.gate_arc()
    welder.arc()
    welder.persist_tension(90.0, 1.05)
    record = welder.splice()
    assert record.position == pytest.approx(88.0)
    assert record.heat_input == pytest.approx(24.0 * 300.0 / 1.5)
    assert welder.state() == WeldState.SPLICED
    assert welder.store.exists("weld.record")
    assert welder.store.exists("weld.seam." + record.seam_id)
    assert welder.seam_id() == record.seam_id


def test_splice_requires_a_running_arc(tmp_path) -> None:
    welder, _ = build(tmp_path)
    with pytest.raises(WeldError) as caught:
        welder.splice()
    assert caught.value.code is WeldErrorCode.ARC_BLOCKED


def test_power_validation(tmp_path) -> None:
    welder, _ = build(tmp_path)
    with pytest.raises(WeldError) as caught:
        welder.set_power(0.0, 10.0)
    assert caught.value.code is WeldErrorCode.POWER_INVALID
    welder.set_power(24.0, 300.0)
    assert welder.power_state() == (pytest.approx(24.0), pytest.approx(300.0))
    assert welder.heat_input() == 0.0


def test_latch_snapshot_round_trip(tmp_path) -> None:
    welder, _ = build(tmp_path)
    welder.alarm()
    assert welder.alarm_active() and not welder.interlock_ok()
    other = Welder(Aligner(), welder.store, EventBus())
    other.restore_latch(LatchSnapshot(interlock=True, alarm=True))
    assert other.alarm_active() and not other.interlock_ok()


def test_seam_history_is_newest_first(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=10.0, at=utcnow())
    for position in (10.0, 20.0, 30.0):
        aligner.confirm = Confirm(ok=True, position=position, at=utcnow())
        welder.gate_arc()
        welder.arc()
        welder.splice()
    history = welder.seam_history(2)
    assert len(history) == 2
    assert history[0].at >= history[1].at


def test_arc_post_splice_regates_on_the_live_confirmation(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=50.0, at=utcnow())
    welder.gate_arc()
    welder.arc()
    welder.splice()
    aligner.confirm = Confirm(ok=True, position=140.0, at=utcnow())
    welder.arc_post_splice()
    assert welder.track_point() == pytest.approx(140.0)


def test_snapshot_exposes_the_transition_history(tmp_path) -> None:
    welder, aligner = build(tmp_path)
    aligner.confirm = Confirm(ok=True, position=10.0, at=utcnow())
    welder.gate_arc()
    welder.arc()
    view = welder.snapshot()
    assert view["state"] == WeldState.WELDING
    assert view["transitions"] == [WeldState.IDLE, WeldState.GATED, WeldState.WELDING]
