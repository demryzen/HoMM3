from homm3.abilities import Ability, register_ability
from homm3.effects import EffectResult, effect_from_str
from homm3.enums import EventType, AttackType
from homm3.events.health_processing import StackRebornEvent


@register_ability
class RegenerationAbility(Ability):
    name = "Regeneration"
    main_schema = {
        "hp": "Int|Str",
    }

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.TurnStarted:
            return EffectResult.empty()

        if event.stack_id != self.stack_id:
            return EffectResult.empty()

        stack = controller.battle.id2stack(self.stack_id)
        if stack.is_died():
            return EffectResult.empty()

        hp = None if self["hp"] == "Inf" else self["hp"]
        return controller.apply_heal(stack_id=self.stack_id, hp=hp)


@register_ability
class RepairingAbility(Ability):
    name = "Repairing"
    main_schema = {
        "val": "Int",
    }


@register_ability
class RebirthAbility(Ability):
    name = "Rebirth"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used = False

    def cleanup_states_after_rebirth(self, stack):
        keep = {"DisruptingRay", "AcidCorrosion"}

        active_states = []
        for state in stack.states:
            if state.name in keep:
                active_states.append(state)
                continue
            if state.name == "Poisoned":
                continue
            active_states.append(state)

        stack.states = active_states

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.StackDied:
            return EffectResult.empty()

        if event.stack_id != self.stack_id:
            return EffectResult.empty()

        if self.used:
            return EffectResult.empty()

        stack = controller.battle.id2stack(self.stack_id)

        base = stack.count_base
        guaranteed = base // 5
        probabilistic = base % 5
        n_reborn = guaranteed + int(
            (controller.battle.rng.random(probabilistic) < 0.2).sum()
        )

        if n_reborn <= 0:
            return EffectResult.empty()

        self.used = True
        stack.reborn(n_reborn)

        self.cleanup_states_after_rebirth(stack)
        if controller.battle.turn_queue.current_id != self.stack_id:
            controller.battle.turn_queue.remove(self.stack_id)

        controller.battle.finished = False
        controller.battle.winner = None

        return EffectResult.event(
            StackRebornEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                n_reborn=n_reborn,
            )
        )


@register_ability
class VampirismAbility(Ability):
    name = "Vampirism"

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.DamageApplied:
            return EffectResult.empty()

        if not hasattr(event, "attack_type"):
            return EffectResult.empty()

        if event.attacker_id != self.stack_id:
            return EffectResult.empty()

        if event.attack_type != AttackType.Melee:
            return EffectResult.empty()

        if event.damage_received <= 0:
            return EffectResult.empty()

        return EffectResult.effect(
            effect_from_str(
                "Vampirism",
                params={"hp": event.damage_received},
            ).bind(
                source_id=event.attacker_id,
                target_id=event.defender_id,
            )
        )