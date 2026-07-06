from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class RandomFaerieDragonSpellCastEvent(Event):
    stack_id: str = ""
    stack: str = ""
    spell: str = ""
    type: EventType = EventType.EffectApplied

    def render(self) -> str:
        return f"'{self.stack}' casts random spell: '{self.spell}'"
    