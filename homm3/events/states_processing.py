from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class StateAppliedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    state: str = ""
    type: EventType = EventType.StateApplied

    def render(self) -> str:
        return f"State '{self.state}' is applied to {self.stack}"


@dataclass(slots=True)
class StateRemovedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    state: str = ""
    type: EventType = EventType.StateRemoved

    def render(self) -> str:
        return f"State '{self.state}' is removed from '{self.stack}'"


@dataclass(slots=True)
class StateAlreadyExistsEvent(Event):
    stack_id: str = ""
    stack: str = ""
    state: str = ""
    type: EventType = EventType.StateAlreadyExists

    def render(self) -> str:
        return f"State '{self.state}' is already applied to '{self.stack}'"


@dataclass(slots=True)
class StateProlongedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    state: str = ""
    type: EventType = EventType.StateProlonged

    def render(self) -> str:
        return f"State '{self.state}' is prolonged on '{self.stack}'"
