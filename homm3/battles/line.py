from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

import numpy as np

from homm3.enums import ActionType
from homm3.units import Stack
from homm3.battles import Battle
from homm3.battles.controller import BattleController
from homm3.battles.queue import TurnQueue
from homm3.strategies import Strategy, MeleeStrategy, RangedStrategy
from homm3.strategies.rune_based import RuneBasedStrategy
from homm3.strategies.cast_spells import FaerieSpellCasterStrategy
from homm3.strategies.alternative_actions import HeatStrokeStrategy, MeditationStrategy, HitAndRunStrategy
from homm3.strategies.damage_maximization import CavalryStrategy
from homm3.params import FIELD_DISTANCE, BAD_MORALE_PROBS, GOOD_MORALE_PROBS
from homm3.contexts import ContextFactory, AvailableAction, MoraleContext
from homm3.effects import effect_from_str, Effect, EffectResult
from homm3.events import EventHandler
from homm3.events.battle_steps import BattleStartedEvent, BattleEndedEvent, RoundStartedEvent, RoundEndedEvent, \
    TurnStartedEvent, TurnEndedEvent, TurnSkippedEvent, TurnInfoEvent
from homm3.events.default_actions import ActionSelectedEvent, ActionStartedEvent, ActionEndedEvent
from homm3.events.effects_processing import EffectAppliedEvent


class EventReactionPhase(Enum):
    States = auto()
    Abilities = auto()
    System = auto()


@dataclass(slots=True)
class EventBatchQueueItem:
    events: list


@dataclass(slots=True)
class EventReactionQueueItem:
    event: object
    phase: EventReactionPhase


@dataclass(slots=True)
class EffectQueueItem:
    effect: Effect


@dataclass(slots=True)
class CleanupQueueItem:
    pass


class LineBattleView:
    def __init__(self, battle: "LineBattle"):
        self._battle = battle

    def stack(self, stack_id: str) -> Stack:
        return self._battle.id2stack(stack_id)

    def stacks(self) -> tuple[Stack, ...]:
        return tuple(self._battle.stacks())

    def allies_of(self, stack_id: str) -> tuple[str, ...]:
        return ()

    def enemies_of(self, stack_id: str) -> tuple[str, ...]:
        if stack_id == self._battle.stack1.id:
            return (self._battle.stack2.id,)
        if stack_id == self._battle.stack2.id:
            return (self._battle.stack1.id,)
        raise ValueError(f"Unknown stack id: {stack_id}")

    def distance(self) -> int:
        return self._battle.distance

    def is_adjacent(self) -> bool:
        return self.distance() == 0


class LineBattle(Battle):
    def __init__(
        self,
        stack1: Stack,
        stack2: Stack,
        distance: int | None = None,
        rounds: int | None = None,
        seed: int | None = None,
        use_morale: bool = True,
        use_luck: bool = True,
        verbose: bool = True,
        event_handler: EventHandler | None = None,
    ):
        super().__init__(verbose, event_handler)
        self.stack1 = stack1
        self.stack2 = stack2
        self.use_morale = use_morale
        self.use_luck = use_luck

        self.distance_max = FIELD_DISTANCE if distance is None else distance
        self.stack1.position = self.stack1.size
        self.stack2.position = self.distance_max - self.stack2.size + 1

        self.rng = np.random.default_rng(seed)
        self.controller = BattleController(self)
        self.context_factory = ContextFactory(self)
        self.turn_queue = TurnQueue()
        self.pending = deque()
        self.is_processing_queue = False

        self.winner = None
        self.round_index = 0
        self.rounds_max = 100 if rounds is None else rounds

        if self.stack1.name == self.stack2.name:
            self.stack1.tag = "1"
            self.stack2.tag = "2"

    @property
    def distance(self) -> int:
        return abs(self.stack1.position - self.stack2.position) - 1

    def stacks(self) -> list[Stack]:
        return [self.stack1, self.stack2]

    def view(self) -> LineBattleView:
        return LineBattleView(self)

    def _queue_items(self, items: list, immediate: bool = False):
        if immediate:
            for item in reversed(items):
                self.pending.appendleft(item)
            return

        self.pending.extend(items)

    def _queue_result(self, result: EffectResult, immediate: bool = False, extra_items: list | None = None):
        items = []
        if result.events:
            items.append(EventBatchQueueItem(result.events))
        items.extend(EffectQueueItem(effect) for effect in result.effects)
        if extra_items:
            items.extend(extra_items)
        self._queue_items(items, immediate=immediate)

    def process_effect_result(self, result: EffectResult):
        self._queue_result(result)
        self.drain_queue()

    def process_event_reaction_phase(self, event, phase: EventReactionPhase):
        if not hasattr(self, "controller"):
            return

        next_phase = None
        if phase == EventReactionPhase.States:
            result = self.controller.process_state_event(event)
            next_phase = EventReactionPhase.Abilities
        elif phase == EventReactionPhase.Abilities:
            result = self.controller.process_ability_event(event)
            next_phase = EventReactionPhase.System
        elif phase == EventReactionPhase.System:
            result = self.controller.process_attack_followups(event)
        else:
            raise ValueError(f"Unknown event reaction phase: {phase}")

        extra_items = []
        if next_phase is not None:
            extra_items.append(EventReactionQueueItem(event, next_phase))
        self._queue_result(result, immediate=True, extra_items=extra_items)

    def process_event_reactions(self, event):
        self._queue_items(
            [EventReactionQueueItem(event, EventReactionPhase.States)],
            immediate=True,
        )

    def dispatch_events(self, events):
        if not events:
            return
        self._queue_items([EventBatchQueueItem(events)])
        self.drain_queue()

    def process_event_batch(self, events):
        for event in events:
            self.dispatch(event)
        for event in reversed(events):
            self.pending.appendleft(EventReactionQueueItem(event, EventReactionPhase.States))

    def drain_queue(self):
        if self.is_processing_queue:
            return

        self.is_processing_queue = True
        try:
            while self.pending:
                item = self.pending.popleft()
                if isinstance(item, EventBatchQueueItem):
                    self.process_event_batch(item.events)
                elif isinstance(item, EventReactionQueueItem):
                    self.process_event_reaction_phase(item.event, item.phase)
                elif isinstance(item, EffectQueueItem):
                    self.apply_queued_effect(item.effect)
                elif isinstance(item, CleanupQueueItem):
                    cleanup_result = self.controller.cleanup_states()
                    self._queue_result(cleanup_result, immediate=True)
                else:
                    raise TypeError(f"Unknown battle queue item: {item!r}")
        finally:
            self.is_processing_queue = False

    def get_all_modifiers(self):
        for stack in self.stacks():
            yield from stack.abilities
            yield from stack.states

    def select_strategy(self, stack: Stack) -> Strategy:
        if stack.has_ability("PossessRunes"):
            return RuneBasedStrategy()
        if stack.has_ability("HeatStroke"):
            return HeatStrokeStrategy()
        if stack.has_ability("Meditation"):
            return MeditationStrategy()
        if stack.has_ability("HitAndRun"):
            return HitAndRunStrategy()
        if stack.name == "Faerie Dragon":
            return FaerieSpellCasterStrategy()
        if stack.has_ability("JoustingBonus"):
            return CavalryStrategy()
        if stack.shots > 0:
            return RangedStrategy()
        return MeleeStrategy()

    def prepare_turn(self, stack: Stack):
        stack.actions_left = 1

    def prepare_round(self):
        for stack in self.stacks():
            stack.prepare_round()

    def prepare_battle(self):
        for stack in self.stacks():
            stack.prepare_battle()
        for stack in self.stacks():
            stack.strategy = self.select_strategy(stack)
        self.winner = None
        self.round_index = 0

    def end_action(self, stack: Stack):
        stack.run_up = 0
        stack.actions_left -= 1

    def is_bad_morale(self, morale_ctx: MoraleContext) -> bool:
        if not self.use_morale:
            return False
        morale = morale_ctx.morale.total()
        if morale >= 0:
            return False
        morale = min(abs(morale), 3)
        return self.rng.random() < BAD_MORALE_PROBS[morale - 1]

    def is_good_morale(self, stack: Stack, morale_ctx: MoraleContext) -> bool:
        if not self.use_morale:
            return False
        if stack.extra_turn:
            return False
        morale = morale_ctx.morale.total()
        if morale <= 0:
            return False
        morale = min(morale, 3)
        return self.rng.random() < GOOD_MORALE_PROBS[morale - 1]

    def apply_queued_effect(self, effect: Effect):
        blocked_event = self.controller.check_effect_blocked(effect)
        if blocked_event is not None:
            self._queue_items([EventBatchQueueItem([blocked_event])], immediate=True)
            return

        result = effect.apply(self.controller)
        if effect.log_applying:
            target = self.id2stack(effect.target_id) if effect.target_id is not None else None
            result.events.insert(
                0,
                EffectAppliedEvent(
                    stack_id="" if target is None else target.id,
                    stack="" if target is None else target.name_count,
                    effect=str(effect) if effect.log_label is None else effect.log_label,
                )
            )
        self._queue_result(result, immediate=True, extra_items=[CleanupQueueItem()])

    def apply_effect(self, effect: Effect):
        self._queue_items([EffectQueueItem(effect)])
        self.drain_queue()

    def apply_good_morale(self, stack: Stack):
        self.apply_effect(effect_from_str("GoodMorale").bind(target_id=stack.id))

    def apply_bad_morale(self, stack: Stack):
        self.apply_effect(effect_from_str("BadMorale").bind(target_id=stack.id))

    def apply_action(self, stack: Stack, action: AvailableAction):
        self.dispatch_events([
            ActionSelectedEvent(
                stack_id=stack.id,
                target_id=action.target_id,
                stack=stack.name_count,
                action=action.type,
                is_free=action.is_free,
            )
        ])

        effect = effect_from_str(action.effect, params=action.params).bind(
            source_id=action.source_id,
            target_id=action.target_id or action.source_id,
        )

        self.dispatch_events([
            ActionStartedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                action_type=action.type,
            )
        ])

        self.apply_effect(effect)

        if (action.ability is not None) and hasattr(action.ability, "mark_used"):
            action.ability.mark_used()

        self.dispatch_events([
            ActionEndedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                action_type=action.type,
            )
        ])

    def perform_action(self, stack: Stack) -> AvailableAction | None:
        action_ctx = self.context_factory.make_action_context(stack.id)

        regular_actions = [action for action in action_ctx.actions if not action.is_free]
        if not regular_actions:
            self.dispatch_events([
                TurnSkippedEvent(
                    stack_id=stack.id,
                    stack=stack.name_count,
                    reason=", ".join(action_ctx.reasons),
                )
            ])
            return None

        action, free_actions = stack.strategy.choose_actions(action_ctx, self.view())

        for free_action in free_actions:
            self.apply_action(stack, free_action)

        self.apply_action(stack, action)
        self.end_action(stack)

        return action

    def perform_turn(self, stack_id: str):
        stack = self.id2stack(stack_id)
        if stack.is_died():
            return
        self.prepare_turn(stack)
        morale_ctx = self.context_factory.make_morale_context(stack_id)

        self.dispatch_events([TurnStartedEvent(stack_id=stack.id, stack=stack.name_count)])
        self.dispatch(
            TurnInfoEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                distance=self.distance,
                health=stack.health,
                health_max=stack.health_base,
                morale_formula=morale_ctx.morale.to_str(result=True),
            )
        )

        if self.is_bad_morale(morale_ctx):
            self.apply_bad_morale(stack)

        while stack.actions_left > 0:
            action = self.perform_action(stack)
            if (action is None) or self.finished:
                break
            if action.type in {ActionType.Wait, ActionType.Defense}:
                break
            if (action.ability is not None) and (action.ability.name == "Meditation"):
                break
            if self.is_good_morale(stack, morale_ctx):
                self.apply_good_morale(stack)

        self.dispatch_events([TurnEndedEvent(stack_id=stack.id, stack=stack.name_count)])

    def run(self):
        self.prepare_battle()
        self.dispatch_events([BattleStartedEvent(
            stack1_id=self.stack1.id,
            stack2_id=self.stack2.id,
            stack1=self.stack1.name_count,
            stack2=self.stack2.name_count,
        )])

        for round_index in range(1, self.rounds_max + 1):
            if self.finished:
                break

            self.prepare_round()
            self.round_index = round_index
            self.turn_queue.start_round(self.stacks())
            self.dispatch_events([RoundStartedEvent(index=round_index)])

            while True:
                stack_id = self.turn_queue.next()
                if stack_id is None:
                    break

                self.perform_turn(stack_id)

                if self.finished:
                    break

            self.dispatch_events([RoundEndedEvent(index=round_index)])

        self.dispatch_events([BattleEndedEvent(
            winner_id=None if self.winner is None else self.winner.id,
            winner=None if self.winner is None else self.winner.name_count
        )])
