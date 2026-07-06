from dataclasses import dataclass

from homm3.events import Event, render_separator
from homm3.enums import EventType


@dataclass(slots=True)
class BattleStartedEvent(Event):
    stack1_id: str = ""
    stack2_id: str = ""
    stack1: str = ""
    stack2: str = ""
    type: EventType = EventType.BattleStarted

    def render(self) -> str:
        return f"Battle starts!\n'{self.stack1}' VS '{self.stack2}'"


@dataclass(slots=True)
class BattleEndedEvent(Event):
    winner_id: str | None = None
    winner: str | None = None
    type: EventType = EventType.BattleEnded

    def render(self) -> str:
        s = "\n" + render_separator("", sep_symbol="=") + "\nBattle finished!\n"
        if self.winner is None:
            s += "No winner. Both stacks died."
        else:
            s += f"'{self.winner}' wins!"
        return s


@dataclass(slots=True)
class RoundStartedEvent(Event):
    index: int = 0
    type: EventType = EventType.RoundStarted

    def render(self) -> str:
        return "\n" + render_separator(f" Round {self.index} ", sep_symbol="=")


@dataclass(slots=True)
class RoundEndedEvent(Event):
    index: int = 0
    log: bool = False
    type: EventType = EventType.RoundEnded


@dataclass(slots=True)
class TurnInfoEvent(Event):
    stack_id: str = ""
    stack: str = ""
    distance: int = 0
    health: int = 0
    health_max: int = 0
    morale_formula: str = ""
    type: EventType | None = None

    def render(self) -> str:
        return "\n".join([
            f"Distance: {self.distance}",
            f"Health: {self.health}/{self.health_max}",
            f"Morale: {self.morale_formula}"
        ])


@dataclass(slots=True)
class TurnStartedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    type: EventType = EventType.TurnStarted

    def render(self) -> str:
        return render_separator(f" {self.stack} turn ", sep_symbol="-")


@dataclass(slots=True)
class TurnSkippedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    reason: str = ""
    type: EventType = EventType.TurnSkipped

    def render(self) -> str:
        return f"'{self.stack}' skips turn: {self.reason}"


@dataclass(slots=True)
class TurnEndedEvent(Event):
    stack_id: str = ""
    stack: str = ""
    type: EventType = EventType.TurnEnded

    def render(self) -> str:
        return f"Turn ended"
