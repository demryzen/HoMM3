from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class RuneLevelIncreasedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    delta: int = 0
    level: int = 0
    type: EventType = EventType.RuneLevelIncreased

    def render(self) -> str:
        return f"'{self.stack}' increased Rune-level on {self.delta} points. Current Rune-level={self.level}"