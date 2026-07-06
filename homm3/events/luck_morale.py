from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class GoodMoraleTriggeredEvent(Event):
    stack_id: str = ""
    stack: str = ""
    type: EventType = EventType.GoodMoraleTriggered

    def render(self) -> str:
        return "Extra turn because of good morale!"


@dataclass(slots=True)
class BadMoraleTriggeredEvent(Event):
    stack_id: str = ""
    stack: str = ""
    type: EventType = EventType.BadMoraleTriggered

    def render(self) -> str:
        return f"'{self.stack}' skips turn because of bad morale"