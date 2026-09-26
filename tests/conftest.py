"""Shared fixtures for the console and equipment tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from linecontrol.console.app import create_app
from linecontrol.line.machine import Line

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


@pytest.fixture()
def line(tmp_path: Path) -> Line:
    instance = Line(tmp_path)
    instance.recover()
    return instance


@pytest.fixture()
def client(line: Line):
    return create_app(line, WEB_ROOT).test_client()
