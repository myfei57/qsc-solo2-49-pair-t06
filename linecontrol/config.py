"""Command line configuration for the service."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

#: Default listen address, data directory and static web root.
DEFAULT_ADDR = ":8080"
DEFAULT_DATA_DIR = "./data"
DEFAULT_WEB_DIR = "./web"

#: Host used when the address carries only a port.
DEFAULT_HOST = "0.0.0.0"


@dataclass(frozen=True, slots=True)
class Config:
    addr: str = DEFAULT_ADDR
    data_dir: str = DEFAULT_DATA_DIR
    web_dir: str = DEFAULT_WEB_DIR

    def host_port(self) -> tuple[str, int]:
        """Split ``host:port``; a bare ``:port`` binds every interface."""

        raw = self.addr.strip()
        if not raw:
            raise ValueError("listen address is empty")
        host, separator, port_text = raw.rpartition(":")
        if not separator:
            host, port_text = DEFAULT_HOST, raw
        port = int(port_text)
        if port <= 0 or port > 65535:
            raise ValueError(f"port out of range: {port}")
        return (host or DEFAULT_HOST), port

    def web_root(self) -> Path:
        return Path(self.web_dir).resolve()

    def data_root(self) -> Path:
        return Path(self.data_dir).resolve()


def parse_args(argv: list[str] | None = None) -> Config:
    parser = argparse.ArgumentParser(prog="linecontrol")
    parser.add_argument("--addr", default=DEFAULT_ADDR, help="listen address")
    parser.add_argument("--data", default=DEFAULT_DATA_DIR, help="data directory")
    parser.add_argument("--web", default=DEFAULT_WEB_DIR, help="frontend directory")
    parsed = parser.parse_args(argv)
    return Config(addr=parsed.addr, data_dir=parsed.data, web_dir=parsed.web)
