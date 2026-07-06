from abc import ABC, abstractmethod
from typing import Protocol

from homm3.events import EventHandler, Event, DefaultLogger
from homm3.units import Stack


class BattleView(Protocol):
    def stack(self, stack_id: str) -> Stack:
        pass

    def stacks(self) -> tuple[Stack, ...]:
        pass

    def allies_of(self, stack_id: str) -> tuple[str, ...]:
        pass

    def enemies_of(self, stack_id: str) -> tuple[str, ...]:
        pass

    def distance(self, stack_id: str, other_id: str) -> int:
        pass

    def is_adjacent(self, stack_id: str, other_id: str) -> bool:
        pass


class Battle(ABC):
    def __init__(
        self,
        verbose: bool = True,
        event_handler: EventHandler | None = None,
    ):
        self.verbose = verbose
        self.event_handler = event_handler or EventHandler(logger=DefaultLogger())
        self.finished = False

        if not self.verbose:
            self.event_handler.logger = None

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stacks(self) -> list[Stack]:
        pass

    @abstractmethod
    def view(self) -> BattleView:
        pass

    def dispatch(self, event: Event):
        self.event_handler.dispatch(event)

    def id2stack(self, stack_id: str) -> Stack:
        for stack in self.stacks():
            if stack.id == stack_id:
                return stack
        raise ValueError(f"Unknown stack id: {stack_id}")
