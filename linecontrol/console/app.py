"""Flask application factory for the console."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from ..line.machine import Line
from .api import Api, ApiParamError

Handler = Callable[[object], dict[str, object]]

#: Content types served from the static web root.
STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


def _route_table(api: Api) -> tuple[tuple[str, str, Handler], ...]:
    """Pair each URL rule with the bound handler that serves it."""

    return (
        ("/api/state", "GET", api.state),
        ("/api/report", "GET", api.report),
        ("/api/sequence", "GET", api.sequence),
        ("/api/sequence/clear", "POST", api.sequence_clear),
        ("/api/machines", "GET", api.machines),
        ("/api/bus", "GET", api.bus_view),
        ("/api/store", "GET", api.store_view),
        ("/api/events", "GET", api.events),
        ("/api/audit", "GET", api.audit),
        ("/api/audit/summary", "GET", api.audit_summary),
        ("/api/weld/confirm", "POST", api.weld_confirm),
        ("/api/weld/splice", "POST", api.weld_splice),
        ("/api/weld/power", "POST", api.weld_power),
        ("/api/weld/seams", "GET", api.weld_seams),
        ("/api/weld/alarm", "POST", api.weld_alarm),
        ("/api/weld/clear", "POST", api.weld_clear),
        ("/api/weld/release", "POST", api.weld_release),
        ("/api/tension/calibrate", "POST", api.tension_calibrate),
        ("/api/tension/ramp", "POST", api.tension_ramp),
        ("/api/tension/persisted", "GET", api.tension_persisted),
        ("/api/pump/start", "POST", api.pump_start),
        ("/api/pump/resume", "POST", api.pump_resume),
        ("/api/pump/replenish", "POST", api.pump_replenish),
        ("/api/pickle/calibrate", "POST", api.pickle_calibrate),
        ("/api/dry/heat", "POST", api.dry_heat),
        ("/api/dry/dew", "POST", api.dry_dew),
        ("/api/dry/heat-target", "POST", api.dry_heat_target),
        ("/api/dry/reheat", "POST", api.dry_reheat),
        ("/api/exit/coil-change", "POST", api.coil_change),
        ("/api/exit/taper", "POST", api.exit_taper),
        ("/api/exit/weight", "POST", api.exit_weight),
        ("/api/exit/shear-offset", "POST", api.shear_offset),
        ("/api/entry/offset", "POST", api.entry_offset),
        ("/api/entry/correct", "POST", api.entry_correct),
        ("/api/entry/sample", "POST", api.entry_sample),
        ("/api/head/track", "POST", api.head_track),
        ("/api/strip/advance", "POST", api.strip_advance),
        ("/api/strip/speed", "POST", api.strip_speed),
        ("/api/strip/sag", "GET", api.strip_sag),
        ("/api/strip/eta", "GET", api.strip_eta),
        ("/api/stop", "POST", api.stop),
        ("/api/cycle", "POST", api.cycle),
    )


def _error_payload(error: Exception) -> dict[str, object]:
    payload: dict[str, object] = {"ok": False, "error": str(error)}
    describe = getattr(error, "to_dict", None)
    if callable(describe):
        payload["detail"] = describe()
    return payload


def _bind(handler: Handler) -> Callable[[], tuple[Response, int]]:
    """Wrap a handler so parameter and domain failures become JSON replies."""

    def view() -> tuple[Response, int]:
        try:
            payload = handler(request)
        except ApiParamError as error:
            return jsonify({"ok": False, "error": str(error)}), 400
        except RuntimeError as error:
            return jsonify(_error_payload(error)), 409
        return jsonify(payload), 200

    view.__name__ = getattr(handler, "__name__", "handler")
    view.__doc__ = getattr(handler, "__doc__", None)
    return view


def create_app(line: Line, web_dir: str | Path) -> Flask:
    """Build the console application around an initialised line."""

    root = Path(web_dir).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"web root is not a directory: {root}")

    api = Api(line)
    app = Flask(__name__, static_folder=None)
    app.config["LINE_API"] = api

    for rule, method, handler in _route_table(api):
        app.add_url_rule(
            rule,
            endpoint=handler.__name__,
            view_func=_bind(handler),
            methods=[method],
        )

    def index() -> Response:
        return send_from_directory(root, "index.html")

    def assets(filename: str) -> Response:
        suffix = Path(filename).suffix.lower()
        return send_from_directory(root, filename, mimetype=STATIC_TYPES.get(suffix))

    app.add_url_rule("/", endpoint="index", view_func=index)
    app.add_url_rule("/<path:filename>", endpoint="assets", view_func=assets)
    return app
