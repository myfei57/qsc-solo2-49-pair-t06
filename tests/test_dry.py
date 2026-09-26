"""Dryer exhaust gate, heat profile and re-heat path."""

from __future__ import annotations

import pytest

from linecontrol.bus import EventBus
from linecontrol.dry.dryer import Dryer
from linecontrol.dry.errors import DryerError, DryerErrorCode
from linecontrol.dry.state import DryerState, MAX_DEW_POINT


class Exhaust:
    def __init__(self) -> None:
        self.established = False

    def __call__(self) -> bool:
        return self.established


def build() -> tuple[Dryer, Exhaust]:
    exhaust = Exhaust()
    return Dryer(exhaust, EventBus()), exhaust


def test_heat_requires_exhaust() -> None:
    dryer, _ = build()
    with pytest.raises(DryerError) as caught:
        dryer.heat_gate()
    assert caught.value.code is DryerErrorCode.NO_EXHAUST
    with pytest.raises(DryerError):
        dryer.heat()
    assert dryer.data.heating() is False


def test_heat_cycle_records_temperature_and_session() -> None:
    dryer, exhaust = build()
    exhaust.established = True
    dryer.heat()
    assert dryer.data.heating() is True
    assert dryer.temp() == pytest.approx(120.0)
    assert dryer.heat_cycles() == 1
    assert dryer.session_seconds() >= 0.0


def test_reheat_is_gated_as_well() -> None:
    dryer, exhaust = build()
    exhaust.established = True
    dryer.heat()
    exhaust.established = False
    with pytest.raises(DryerError) as caught:
        dryer.reheat()
    assert caught.value.code is DryerErrorCode.NO_EXHAUST
    exhaust.established = True
    dryer.reheat()
    assert dryer.heat_cycles() == 2


def test_dew_guard_blocks_a_wet_chamber() -> None:
    dryer, _ = build()
    dryer.set_dew_point(MAX_DEW_POINT + 5)
    with pytest.raises(DryerError) as caught:
        dryer.dew_guard()
    assert caught.value.code is DryerErrorCode.DEW_HIGH
    dryer.set_dew_point(-10.0)
    dryer.dew_guard()
    assert dryer.dew_point() == pytest.approx(-10.0)


def test_heat_profile_is_rate_limited() -> None:
    dryer, exhaust = build()
    exhaust.established = True
    dryer.heat()
    next_temp = dryer.heat_profile(180.0)
    assert next_temp == pytest.approx(135.0)
    dryer.apply_profile(next_temp)
    assert dryer.temp() == pytest.approx(135.0)
    assert dryer.data.machine.state == DryerState.HEATING


def test_heat_profile_range_check() -> None:
    dryer, _ = build()
    with pytest.raises(DryerError) as caught:
        dryer.heat_profile(20.0)
    assert caught.value.code is DryerErrorCode.TEMP_RANGE
    with pytest.raises(DryerError):
        dryer.heat_profile(400.0)


def test_snapshot_view() -> None:
    dryer, exhaust = build()
    exhaust.established = True
    dryer.heat()
    view = dryer.snapshot()
    assert view["heating"] is True
    assert view["state"] == DryerState.HEATING
    assert view["cycles"] == 1
