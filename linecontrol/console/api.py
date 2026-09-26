"""JSON handlers backing the console endpoints."""

from __future__ import annotations

from flask import Request

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..line.machine import Line
from ..line.workflow import CycleInput
from ..store.snapshot import snapshot_type_names

#: Number of recent process events kept for the live event endpoint.
STREAM_LIMIT = 300

#: Default page size for audit queries.
DEFAULT_AUDIT_LIMIT = 50

#: Default page size for the seam history.
DEFAULT_SEAM_LIMIT = 20


class ApiParamError(ValueError):
    """Raised when a query parameter is missing or malformed."""

    def __init__(self, name: str, raw: str) -> None:
        super().__init__(f"invalid value for {name!r}: {raw!r}")
        self.name = name
        self.raw = raw


def float_param(request: Request, name: str) -> float:
    raw = request.args.get(name, "")
    if raw == "":
        raise ApiParamError(name, raw)
    try:
        return float(raw)
    except ValueError as error:
        raise ApiParamError(name, raw) from error


def int_param(request: Request, name: str, default: int) -> int:
    raw = request.args.get(name, "")
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ApiParamError(name, raw) from error


class Api:
    """Holds the line plus the event stream shown on the overview page."""

    def __init__(self, line: Line) -> None:
        self.line = line
        self.stream: list[Event] = []
        self._unsubscribe = line.subscribe(self._collect)

    def _collect(self, event: Event) -> None:
        self.stream.append(event)
        if len(self.stream) > STREAM_LIMIT:
            del self.stream[: len(self.stream) - STREAM_LIMIT]

    def close(self) -> None:
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe = []
        self.line.close()

    def stream_view(self) -> list[dict[str, object]]:
        return [event.to_dict() for event in self.stream]

    # -- read endpoints -------------------------------------------------

    def state(self, request: Request) -> dict[str, object]:
        return {"ok": True, "state": self.line.state()}

    def report(self, request: Request) -> dict[str, object]:
        return {"ok": True, "report": self.line.run_report()}

    def sequence(self, request: Request) -> dict[str, object]:
        return {"ok": True, "sequence": self.line.sequence_snapshot()}

    def sequence_clear(self, request: Request) -> dict[str, object]:
        self.line.clear_sequence()
        return {"ok": True}

    def machines(self, request: Request) -> dict[str, object]:
        return {
            "ok": True,
            "machines": {
                "weld": {
                    "name": self.line.weld.machine.name,
                    "state": self.line.weld.machine.state,
                    "next": list(self.line.weld.machine.reachable()),
                    "history": list(self.line.weld.machine.history()),
                },
                "pump": {
                    "name": self.line.pump.data.machine.name,
                    "state": self.line.pump.data.machine.state,
                    "next": list(self.line.pump.data.machine.reachable()),
                    "history": list(self.line.pump.data.machine.history()),
                },
                "dryer": {
                    "name": self.line.dry.data.machine.name,
                    "state": self.line.dry.data.machine.state,
                    "next": list(self.line.dry.data.machine.reachable()),
                    "history": list(self.line.dry.data.machine.history()),
                },
                "tension": {
                    "name": self.line.tension.data.machine.name,
                    "state": self.line.tension.data.machine.state,
                    "next": list(self.line.tension.data.machine.reachable()),
                    "history": list(self.line.tension.data.machine.history()),
                },
            },
        }

    def bus_view(self, request: Request) -> dict[str, object]:
        return {
            "ok": True,
            "delivered": self.line.bus.delivered(),
            "subscribers": {
                kind.value: self.line.bus.subscribers(kind) for kind in EventKind
            },
        }

    def store_view(self, request: Request) -> dict[str, object]:
        keys = self.line.store.list()
        return {
            "ok": True,
            "directory": self.line.store.directory,
            "keys": keys,
            "backup": list(self.line.store.backup_files()),
            "recordTypes": list(snapshot_type_names()),
        }

    def events(self, request: Request) -> dict[str, object]:
        return {"ok": True, "events": self.stream_view()}

    def audit(self, request: Request) -> dict[str, object]:
        limit = int_param(request, "limit", DEFAULT_AUDIT_LIMIT)
        raw_kind = request.args.get("kind", "")
        if raw_kind:
            events = self.line.audit_query(EventKind(raw_kind), limit)
        else:
            events = self.line.audit_query(None, limit)
        return {"ok": True, "events": [event.to_dict() for event in events]}

    def audit_summary(self, request: Request) -> dict[str, object]:
        return {"ok": True, "summary": self.line.audit.summary()}

    def weld_seams(self, request: Request) -> dict[str, object]:
        limit = int_param(request, "limit", DEFAULT_SEAM_LIMIT)
        seams = self.line.weld_seams(limit)
        return {"ok": True, "seams": [seam.to_dict() for seam in seams]}

    def tension_persisted(self, request: Request) -> dict[str, object]:
        snapshot, ok = self.line.persisted_tension()
        return {"ok": True, "persisted": ok, "snapshot": snapshot.to_dict()}

    def strip_sag(self, request: Request) -> dict[str, object]:
        return {"ok": True, "sag": self.line.sag()}

    def strip_eta(self, request: Request) -> dict[str, object]:
        return {"ok": True, "eta": self.line.track_eta(float_param(request, "target"))}

    # -- write endpoints ------------------------------------------------

    def weld_confirm(self, request: Request) -> dict[str, object]:
        self.line.weld_and_speedup()
        return {"ok": True, "state": self.line.weld.state()}

    def weld_splice(self, request: Request) -> dict[str, object]:
        self.line.splice_and_refresh(float_param(request, "pos"))
        return {"ok": True, "seam": self.line.weld.seam_id()}

    def weld_power(self, request: Request) -> dict[str, object]:
        self.line.set_weld_power(
            float_param(request, "voltage"),
            float_param(request, "current"),
        )
        return {"ok": True}

    def weld_alarm(self, request: Request) -> dict[str, object]:
        self.line.alarm_overcurrent()
        return {"ok": True, "alarms": self.line.audit.active_alarms()}

    def weld_clear(self, request: Request) -> dict[str, object]:
        cleared = self.line.clear_weld_alarm()
        return {"ok": True, "cleared": cleared}

    def weld_release(self, request: Request) -> dict[str, object]:
        self.line.splice_release()
        return {"ok": True}

    def tension_calibrate(self, request: Request) -> dict[str, object]:
        changed = self.line.recalibrate_tension(float_param(request, "gain"))
        return {"ok": True, "changed": changed, "gain": self.line.tension.gain()}

    def tension_ramp(self, request: Request) -> dict[str, object]:
        plan = self.line.ramp_speed(float_param(request, "target"))
        return {"ok": True, "steps": len(plan.steps), "speed": self.line.tension.speed()}

    def pump_start(self, request: Request) -> dict[str, object]:
        self.line.start_acid_loop(float_param(request, "level"))
        return {"ok": True}

    def pump_resume(self, request: Request) -> dict[str, object]:
        self.line.resume_acid_loop(float_param(request, "level"))
        return {"ok": True}

    def pump_replenish(self, request: Request) -> dict[str, object]:
        plan = self.line.replenish_acid(
            float_param(request, "volume"),
            float_param(request, "target"),
        )
        return {"ok": True, "plan": plan.to_dict()}

    def pickle_calibrate(self, request: Request) -> dict[str, object]:
        self.line.calibrate_acid(float_param(request, "offset"))
        return {"ok": True, "concentration": self.line.pickle.concentration()}

    def dry_heat(self, request: Request) -> dict[str, object]:
        self.line.heat_dryer_and_coil()
        return {"ok": True}

    def dry_dew(self, request: Request) -> dict[str, object]:
        self.line.set_dryer_dew(float_param(request, "value"))
        return {"ok": True, "dew": self.line.dry.dew_point()}

    def dry_heat_target(self, request: Request) -> dict[str, object]:
        temp = self.line.set_dryer_heat(float_param(request, "temp"))
        return {"ok": True, "temp": temp}

    def dry_reheat(self, request: Request) -> dict[str, object]:
        self.line.reheat_dryer()
        return {"ok": True, "cycles": self.line.dry.heat_cycles()}

    def coil_change(self, request: Request) -> dict[str, object]:
        self.line.coil_change()
        return {"ok": True}

    def exit_taper(self, request: Request) -> dict[str, object]:
        taper = self.line.taper_exit(
            float_param(request, "base"),
            float_param(request, "diameter"),
        )
        return {"ok": True, "taper": taper}

    def exit_weight(self, request: Request) -> dict[str, object]:
        weight = self.line.coil_weight(
            float_param(request, "entry"),
            float_param(request, "exit"),
            float_param(request, "width"),
            float_param(request, "length"),
        )
        return {"ok": True, "weight": weight}

    def shear_offset(self, request: Request) -> dict[str, object]:
        self.line.set_shear_offset(float_param(request, "offset"))
        return {"ok": True, "offset": self.line.exit.shear_offset()}

    def entry_offset(self, request: Request) -> dict[str, object]:
        self.line.align_offset(float_param(request, "value"))
        return {"ok": True, "centerError": self.line.entry.center_error()}

    def entry_correct(self, request: Request) -> dict[str, object]:
        return {"ok": True, "applied": self.line.correct_head()}

    def entry_sample(self, request: Request) -> dict[str, object]:
        self.line.push_head_sample(float_param(request, "value"))
        return {"ok": True, "count": self.line.entry.sample_count()}

    def strip_advance(self, request: Request) -> dict[str, object]:
        track = self.line.advance_strip(float_param(request, "delta"))
        return {"ok": True, "track": track}

    def strip_speed(self, request: Request) -> dict[str, object]:
        self.line.set_strip_speed(float_param(request, "speed"))
        return {"ok": True, "speed": self.line.strip.speed()}

    def head_track(self, request: Request) -> dict[str, object]:
        self.line.track_head(float_param(request, "delta"))
        return {"ok": True, "head": self.line.entry.head_position()}

    def stop(self, request: Request) -> dict[str, object]:
        self.line.stop_line()
        return {"ok": True}

    def cycle(self, request: Request) -> dict[str, object]:
        coil_id = request.args.get("coil", "")
        if not coil_id:
            raise ApiParamError("coil", coil_id)
        payload = CycleInput(
            coil_id=coil_id,
            target=float_param(request, "target"),
            level=float_param(request, "level"),
            voltage=float_param(request, "voltage"),
            current=float_param(request, "current"),
            speed=float_param(request, "speed"),
        )
        self.line.production_cycle(payload)
        return {"ok": True, "sequence": self.line.sequence_snapshot()}
