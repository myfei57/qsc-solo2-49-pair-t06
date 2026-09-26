"""Service entry point."""

from __future__ import annotations

import logging
import sys

from .config import parse_args
from .console.app import create_app
from .console.server import serve
from .line.machine import Line


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = parse_args(argv)
    try:
        config.host_port()
    except ValueError as error:
        print(f"linecontrol: {error}", file=sys.stderr)
        return 2

    line = Line(config.data_root())
    recovery = line.recover()
    logging.getLogger("linecontrol").info(
        "recovered %d snapshots", len(recovery.loaded)
    )
    app = create_app(line, config.web_root())
    serve(config, app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
