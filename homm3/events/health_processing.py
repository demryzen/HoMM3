from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType


@dataclass(slots=True)
class StackHealedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    hp: int | None = None
    hp_restored: int = 0
    type: EventType = EventType.StackHealed

    def render(self) -> str:
        if self.hp is None:
            return f"'{self.stack}' is fully healed ({self.hp_restored} hp restored)"
        return f"'{self.stack}' is healed by {self.hp_restored} hp"


@dataclass(slots=True)
class StackMaxHealthChangedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    reason: str = ""
    health_before: int = 0
    health_max_before: int = 0
    health_after: int = 0
    health_max_after: int = 0
    type: EventType = EventType.DamageApplied

    def render(self) -> str:
        return (
            f"{self.reason} changed '{self.stack}' health: "
            f"{self.health_before}/{self.health_max_before} -> "
            f"{self.health_after}/{self.health_max_after}"
        )


@dataclass(slots=True)
class StackRebornEvent(Event):
    stack_id: str = ""
    stack: str = ""
    n_reborn: int = 0
    type: EventType = EventType.StackReborn

    def render(self) -> str:
        return f"{self.n_reborn} units of '{self.stack}' reborn"


@dataclass(slots=True)
class VampirismAppliedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    hp: int = 0
    n_resurrected: int = 0
    type: EventType = EventType.StackHealed

    def render(self) -> str:
        return f"'{self.stack}' drains {self.hp} health using vampirism and {self.n_resurrected} units resurrected"