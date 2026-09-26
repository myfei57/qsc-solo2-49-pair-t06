"""WSGI serving helper."""

from __future__ import annotations

import logging

from flask import Flask

from ..config import Config

LOGGER = logging.getLogger("linecontrol.console")


def serve(config: Config, app: Flask) -> None:
    """Run the application until the process is interrupted."""

    host, port = config.host_port()
    LOGGER.info("console listening on %s:%s", host, port)
    api = app.config["LINE_API"]
    try:
        app.run(host=host, port=port, threaded=True, use_reloader=False)
    finally:
        api.close()
