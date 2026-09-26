"""Start-up recovery from the on-disk snapshots."""

from __future__ import annotations

from ..domain.events import Event
from ..domain.kinds import EventKind
from ..domain.phase import Phase
from ..store.recovery import Recovery, collect


class RecoveryOps:
    """Mixed into :class:`~linecontrol.line.machine.Line`."""

    def recover(self) -> Recovery:
        """Rebuild every controller from the newest snapshots.

        The stored gain is applied before the tension setpoint is restored so
        that the roller never runs a restored setpoint against a stale
        baseline.
        """

        self.set_phase(Phase.RECOVERING)
        state = collect(self.store)
        if state.gain > 0:
            self.tension.recalibrate(state.gain)
        self.weld.restore_latch(state.latch)
        self.weld.restore_tension(state.tension)
        self.tension.restore_tension(state.tension)
        self.pickle.restore_acid(state.acid)
        self.pickle.restore_rinse(state.rinse.active)
        self.pump.restore(state.pump)
        self.pump.restore_run(state.run_seconds)
        self.strip.restore_track(state.track)
        self.audit.restore()
        self.audit.flush()
        if state.rinse.active:
            self.pickle.rinse_stop()
        self.exit.recover_lift()
        self.bus.publish(Event(kind=EventKind.RECOVER, source="line", message="recovered"))
        self.set_phase(Phase.IDLE)
        return state
