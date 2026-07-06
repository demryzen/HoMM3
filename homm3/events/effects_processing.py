from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class EffectBlockedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    effect: str = ""
    reason: str = ""
    type: EventType = EventType.EffectBlocked

    def render(self) -> str:
        if self.reason == "Immunity":
            reason = f"'{self.stack}' is immune"
        elif self.reason == "SpellResistance":
            reason = f"'{self.stack}' spell resistance triggered"
        elif self.reason == "TargetFilter":
            reason = f"'{self.stack}' is not a valid target"
        elif self.reason == "AlreadyApplied":
            reason = f"'{self.stack}' already has this effect"
        elif self.reason == "Power":
            reason = f"not enough power of spell"
        else:
            reason = self.reason
        return f"Effect '{str(self.effect)}' blocked: {reason}"


@dataclass(slots=True)
class EffectAppliedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    effect: str = ""
    type: EventType = EventType.EffectApplied

    def render(self) -> str:
        return f"Effect '{self.effect}' applied to {self.stack}"
