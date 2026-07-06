from dataclasses import dataclass, field
from typing import Protocol

from homm3.enums import EventType
from homm3.params import SEPARATOR_LOG_MAXLEN


@dataclass
class Event:
    type: EventType | None = None
    log: bool = True

    def render(self) -> str:
        return ""


class EventLogger(Protocol):
    def log(self, event: Event) -> None:
        pass


class DefaultLogger:
    def log(self, event: Event) -> None:
        message = event.render()
        if message:
            print(message)


@dataclass
class EventHandler:
    logger: EventLogger | None = None
    history: list[Event] = field(default_factory=list)

    def dispatch(self, event: Event):
        self.history.append(event)
        if event.log and (self.logger is not None):
            self.logger.log(event)


def render_separator(msg: str, max_len: int = SEPARATOR_LOG_MAXLEN, sep_symbol: str = "=") -> str:
    return msg.center(max_len, sep_symbol) if len(msg) < max_len else f"{sep_symbol}{msg}{sep_symbol}"
