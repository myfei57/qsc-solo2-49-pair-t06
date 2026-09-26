"""Command line configuration parsing."""

from __future__ import annotations

import pytest

from linecontrol.config import Config, parse_args


def test_defaults() -> None:
    config = parse_args([])
    assert config.addr == ":8080"
    assert config.data_dir == "./data"
    assert config.web_dir == "./web"


def test_overrides() -> None:
    config = parse_args(["--addr", "127.0.0.1:9001", "--data", "/tmp/d", "--web", "/tmp/w"])
    assert config.host_port() == ("127.0.0.1", 9001)
    assert str(config.data_root()).endswith("d")
    assert str(config.web_root()).endswith("w")


def test_bare_port_binds_every_interface() -> None:
    assert Config(addr=":7000").host_port() == ("0.0.0.0", 7000)
    assert Config(addr="7001").host_port() == ("0.0.0.0", 7001)


def test_invalid_addresses_are_rejected() -> None:
    with pytest.raises(ValueError):
        Config(addr="").host_port()
    with pytest.raises(ValueError):
        Config(addr=":0").host_port()
    with pytest.raises(ValueError):
        Config(addr=":99999").host_port()
    with pytest.raises(ValueError):
        Config(addr=":abc").host_port()
