from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import EventType, AttackType


@dataclass(slots=True)
class PhysicalDamageAppliedEvent(Event):
    attacker_id: str = ""
    defender_id: str = ""
    attacker: str = ""
    defender: str = ""
    damage: int = 0
    damage_received: int = 0
    attack_formula: str = ""
    defense_formula: str = ""
    luck_formula: str = ""
    damage_formula: str = ""
    attack_type: AttackType | None = None
    is_retaliation: bool = False
    type: EventType = EventType.DamageApplied

    def render(self) -> str:
        return "\n".join([
            f"\tAttack: {self.attack_formula}",
            f"\tDefense: {self.defense_formula}",
            f"\tLuck: {self.luck_formula}",
            f"\tDamage: {self.damage_formula}",
        ])


@dataclass(slots=True)
class InstantDamageAppliedEvent(Event):
    attacker_id: str = ""
    defender_id: str = ""
    damage: int = 0
    damage_received: int = 0
    damage_formula: str = ""
    type: EventType = EventType.DamageApplied

    def render(self) -> str:
        if self.damage_formula:
            return f"\tDamage: {self.damage_formula}"
        return f"\tDamage: {self.damage}"


@dataclass(slots=True)
class UnitsDiedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    n_died: int = 0
    type: EventType = EventType.UnitsDied

    def render(self) -> str:
        return f"\t{self.n_died} units died"


@dataclass(slots=True)
class StackDiedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    killed_by_id: str = ""
    n_died: int = 0
    type: EventType = EventType.StackDied

    def render(self) -> str:
        return f"'{self.stack}' is died"


@dataclass(slots=True)
class ShotsChangedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    shots: int = 0
    shots_base: int = 0
    type: EventType = EventType.ShotsChanged

    def render(self) -> str:
        return f"\t{self.shots}/{self.shots_base} shots remain"


@dataclass(slots=True)
class StackDetonatedEvent(Event):
    source_id: str = ""
    target_id: str = ""
    source: str = ""
    target: str = ""
    damage: int = 0
    damage_received: int = 0
    type: EventType = EventType.DamageApplied

    def render(self) -> str:
        return f"'{self.source}' detonates and deals {self.damage} damage to '{self.target}'"


@dataclass(slots=True)
class UnitsInstantKilledEvent(Event):
    stack_id: str = ""
    stack: str = ""
    reason: str = ""
    n_killed: int = 0
    type: EventType = EventType.UnitsDied

    def render(self) -> str:
        if self.n_killed > 0:
            msg = f"{self.n_killed} units died"
        else:
            msg = "no one died"
        if self.reason:
            msg = f"{self.reason}: {msg}"
        return f"\t{msg}"
