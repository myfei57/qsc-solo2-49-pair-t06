"""Small explicit state machine used by the equipment controllers."""

from __future__ import annotations

from typing import Iterable, Mapping


class IllegalTransition(RuntimeError):
    """Raised when a controller is asked to jump to a forbidden state."""

    def __init__(self, machine: str, origin: str, target: str) -> None:
        super().__init__(f"{machine}: cannot move from {origin!r} to {target!r}")
        self.machine = machine
        self.origin = origin
        self.target = target


class StateMachine:
    """A transition table with an auditable history.

    The table maps a state to the set of states reachable from it. Building the
    table up front keeps every legal path explicit and lets the controllers
    reject a jump before any side effect happens.
    """

    def __init__(
        self,
        name: str,
        initial: str,
        transitions: Mapping[str, Iterable[str]],
    ) -> None:
        self._name = name
        self._table: dict[str, frozenset[str]] = {
            state: frozenset(targets) for state, targets in transitions.items()
        }
        if initial not in self._table:
            raise ValueError(f"{name}: initial state {initial!r} is not in the table")
        self._state = initial
        self._history: list[str] = [initial]

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return self._state

    def history(self) -> tuple[str, ...]:
        return tuple(self._history)

    def allows(self, target: str) -> bool:
        return target in self._table.get(self._state, frozenset())

    def reachable(self) -> tuple[str, ...]:
        return tuple(sorted(self._table.get(self._state, frozenset())))

    def enter(self, target: str) -> None:
        if target == self._state:
            return
        if not self.allows(target):
            raise IllegalTransition(self._name, self._state, target)
        self._state = target
        self._history.append(target)

    def force(self, target: str) -> None:
        """Restore a state read back from disk without table validation."""

        self._state = target
        self._history.append(target)
