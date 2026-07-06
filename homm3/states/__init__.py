from copy import deepcopy
from typing import Any

from homm3.effects import EffectResult
from homm3.enums import Status, EventType
from homm3.properties import Parametrized
from homm3.registry import Registry


class State(Parametrized):
    name: str = "State"
    cancel: tuple[str, ...] = ()
    cumulative: bool = False
    dispellable: bool = True
    status: Status | None = None

    def __init__(
        self,
        stack_id: str | None = None,
        source_id: str | None = None,
        params: dict[str, Any] | None = None,
    ):
        super().__init__(params=params)
        self.stack_id = stack_id
        self.source_id = source_id
        self.expired = False

    @property
    def key(self) -> tuple:
        return self.name, self.stack_id

    @property
    def rounds(self) -> int | None:
        return self.params.get("rounds")

    @rounds.setter
    def rounds(self, value: int | None):
        if value is None:
            self.params.pop("rounds", None)
        else:
            self.params["rounds"] = value

    def bind(
        self,
        stack_id: str,
        source_id: str | None = None,
    ) -> "State":
        state = deepcopy(self)
        state.stack_id = stack_id
        if source_id is not None:
            state.source_id = source_id
        return state

    def expire(self):
        self.expired = True

    def is_active(self, view) -> bool:
        return not self.expired

    def on_apply(self, controller) -> EffectResult:
        return EffectResult.empty()

    def on_remove(self, controller) -> EffectResult:
        return EffectResult.empty()

    def on_prolong(self, other: "State", controller) -> EffectResult:
        if (self.rounds is not None) and (other.rounds is not None):
            self.rounds += other.rounds
        return EffectResult.empty()

    def on_event(self, event, controller) -> EffectResult:
        if self.rounds == "Inf":
            return EffectResult.empty()

        if (event.type == EventType.RoundEnded) and (self.rounds is not None):
            self.rounds -= 1
            if self.rounds <= 0:
                self.expire()
        return EffectResult.empty()


STATES = Registry(base_cls=State, package_name="homm3.states", object_name="state")


def state_class(name: str) -> type[State] | None:
    return STATES.get(name)


def state_from_str(name: str, params: dict[str, Any] | None = None) -> State:
    return STATES.create(name, params=params)


def register_state(cls=None, *, name: str | None = None, aliases: tuple[str, ...] = ()):
    return STATES.register(cls, name=name, aliases=aliases)
