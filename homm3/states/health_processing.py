import numpy as np

from homm3.effects import EffectResult
from homm3.enums import Status, EventType
from homm3.events.health_processing import StackMaxHealthChangedEvent
from homm3.states import register_state, State


@register_state
class PoisonedState(State):
    name = "Poisoned"
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = 0

    def on_apply(self, controller) -> EffectResult:
        return self.apply_poison(controller)

    def on_prolong(self, other: State, controller) -> EffectResult:
        result = super().on_prolong(other, controller)
        result.extend(self.apply_poison(controller))
        return result

    def on_event(self, event, controller) -> EffectResult:
        result = super().on_event(event, controller)
        if event.type == EventType.RoundStarted:
            result.extend(self.apply_poison(controller))
        return result

    def apply_poison(self, controller) -> EffectResult:
        stack = controller.battle.id2stack(self.stack_id)
        if stack.is_died():
            return EffectResult.empty()
        if stack.health_max <= 1:
            return EffectResult.empty()
        val = self["val"]
        if self.n * val >= 50:
            return EffectResult.empty()
        self.n += 1
        health_before, health_max_before = stack.reduce_health_max(val)
        return EffectResult.event(
            StackMaxHealthChangedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                reason="Poison",
                health_before=health_before,
                health_max_before=health_max_before,
                health_after=stack.health,
                health_max_after=stack.health_max,
            )
        )


@register_state
class AgedState(State):
    name = "Aged"
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def on_apply(self, controller) -> EffectResult:
        return self.apply_ageing(controller)

    def apply_ageing(self, controller) -> EffectResult:
        stack = controller.battle.id2stack(self.stack_id)
        if stack.is_died():
            return EffectResult.empty()

        health_before, health_max_before = stack.reduce_health_max(self["val"])

        return EffectResult.event(
            StackMaxHealthChangedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                reason="Ageing",
                health_before=health_before,
                health_max_before=health_max_before,
                health_after=stack.health,
                health_max_after=stack.health_max,
            )
        )

    def on_remove(self, controller) -> EffectResult:
        stack = controller.battle.id2stack(self.stack_id)
        health_before = stack.health
        health_max_before = stack.health_max

        damage = stack.health_max - stack.health
        stack.health_max = stack.health_base
        stack.health = max(1, stack.health_max - damage)

        return EffectResult.event(
            StackMaxHealthChangedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                reason="Ageing removed",
                health_before=health_before,
                health_max_before=health_max_before,
                health_after=stack.health,
                health_max_after=stack.health_max,
            )
        )