from dataclasses import dataclass

from homm3.events import Event
from homm3.enums import AttackOrder, EventType, AttackType, ActionType


@dataclass(slots=True)
class StackMovedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    speed_formula: str = ""
    steps: int = 0
    type: EventType = EventType.StackMoved

    def render(self) -> str:
        return f"'{self.stack}' moves\n\tMax speed: {self.speed_formula}\n\tSteps: {self.steps}"


@dataclass(slots=True)
class StackReturnedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    steps: int = 0
    type: EventType = EventType.StackMoved

    def render(self) -> str:
        return f"'{self.stack}' returns back\n\tSteps: {self.steps}"


@dataclass(slots=True)
class StackWaitedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    type: EventType = EventType.StackWaited

    def render(self) -> str:
        return f"'{self.stack}' is waiting"


@dataclass(slots=True)
class StackDefendedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    defense_formula: str = ""
    type: EventType = EventType.StackDefended

    def render(self) -> str:
        return f"'{self.stack}' is defending\n\tDefense bonus: {self.defense_formula}"


@dataclass(slots=True)
class AttackStartedEvent(Event):
    attacker_id: str = ""
    defender_id: str = ""
    attacker: str = ""
    defender: str = ""
    attack_name: str = ""
    attack_type: AttackType | None = None
    attack_order: AttackOrder = AttackOrder.Regular
    type: EventType = EventType.AttackStarted

    def render(self) -> str:
        suffix = " again" if self.attack_order == AttackOrder.Additional else ""
        return f"'{self.attacker}' {self.attack_name}{suffix} '{self.defender}'"


@dataclass(slots=True)
class AttackEndedEvent(Event):
    attacker_id: str = ""
    defender_id: str = ""
    attacker: str = ""
    defender: str = ""
    attack_type: AttackType | None = None
    attack_order: AttackOrder = AttackOrder.Regular
    n_died: int = 0
    additional_left: int = 0
    type: EventType = EventType.AttackEnded


@dataclass(slots=True)
class ActionSelectedEvent(Event):
    stack_id: str = ""
    target_id: str = ""
    stack: str = ""
    action: ActionType | None = None
    is_free: bool = False
    type: EventType = EventType.ActionSelected

    def render(self) -> str:
        if self.is_free:
            return f"Selected free action: {self.action}"
        return f"Selected action: {self.action}"


@dataclass(slots=True)
class ActionStartedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    action_type: ActionType | None = None
    log: bool = False
    type: EventType = EventType.ActionStarted


@dataclass(slots=True)
class ActionEndedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    action_type: ActionType | None = None
    log: bool = False
    type: EventType = EventType.ActionEnded
