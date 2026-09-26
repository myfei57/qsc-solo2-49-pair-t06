"""Line controller wiring every equipment area together."""

from __future__ import annotations

from pathlib import Path

from ..audit.logger import Logger
from ..bus import EventBus
from ..domain.phase import Phase
from ..dry.dryer import Dryer
from ..entry.controller import Controller as EntryController
from ..exit.section import Exit
from ..pickle.tank import Tank
from ..pump.pump import Pump
from ..store.filestore import FileStore
from ..strip.strip import Strip
from ..tension.roller import Roller
from ..weld.welder import Welder
from ..store.backup import BackupSummary
from .commands import CommandOps
from .recovery import RecoveryOps
from .sequence import Sequence
from .view import ViewOps
from .workflow import WorkflowOps

#: Tension setpoint applied when the line is first built.
DEFAULT_SETPOINT = 80.0


class Line(WorkflowOps, CommandOps, RecoveryOps, ViewOps):
    """Owns the equipment areas and the cross-area call chains."""

    def __init__(self, data_dir: str | Path) -> None:
        self.store = FileStore(Path(data_dir) / "snap")
        self.bus = EventBus()
        self.audit = Logger(self.store, self.bus)
        self.entry = EntryController(self.bus)
        self.tension = Roller(self.store)
        self.pickle = Tank(self.store, self.bus)
        self.strip = Strip(self.store, self.bus, self.tension.gain, self.pickle.flushed)
        self.pump = Pump(self.pickle, self.store, self.bus, self.strip.stopped)
        self.exit = Exit(self.pickle, self.strip, self.bus)
        self.dry = Dryer(self.exit.exhaust_ok, self.bus)
        self.weld = Welder(self.entry.confirm_state, self.store, self.bus)
        self.entry.set_interlock_provider(self.weld.interlock_ok)
        self.tension.apply_setpoint(DEFAULT_SETPOINT)
        self.phase = Phase.IDLE
        self.coil_no = 0
        self.handle = ""
        self.seq = Sequence()
        self.last_backup: BackupSummary | None = None
        self._audit_unsubscribe = self.subscribe(self.audit.record)

    def set_phase(self, phase: Phase) -> None:
        self.phase = phase
