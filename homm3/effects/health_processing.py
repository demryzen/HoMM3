from homm3.effects import Effect, EffectResult, register_effect
from homm3.effects.states_processing import ApplyStateEffect
from homm3.enums import Status, EffectType, EffectElement, SpellMastery, UnitEntity
from homm3.events.health_processing import VampirismAppliedEvent
from homm3.filters import EntityFilter


@register_effect
class HealEffect(Effect):
    name = "Heal"
    main_schema = {
        "hp": "Int",
    }
    status = Status.Positive
    log_applying = True

    def apply(self, controller) -> EffectResult:
        return controller.apply_heal(stack_id=self.target_id, hp=self["hp"])


@register_effect
class CureEffect(Effect):
    name = "Cure"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int"
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    element = EffectElement.Water
    level = 1
    log_applying = True

    def apply(self, controller) -> EffectResult:
        hp = {
            SpellMastery.No: 10,
            SpellMastery.Basic: 10,
            SpellMastery.Advanced: 20,
            SpellMastery.Expert: 30,
        }[self["mastery"]]
        result = controller.apply_heal(stack_id=self.target_id, hp=5 * self["power"] + hp)
        stack = controller.battle.id2stack(self.target_id)
        for state in list(stack.states):
            if state.status == Status.Negative and state.dispellable:
                result.extend(controller.remove_state(self.target_id, state.name))
        return result


@register_effect
class PoisonEffect(ApplyStateEffect):
    name = "Poison"
    states = ("Poisoned",)
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 1
    cumulative = True
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )


@register_effect
class AgeingEffect(ApplyStateEffect):
    name = "Ageing"
    states = ("Aged",)
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 5
    cumulative = True
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )


@register_effect
class VampirismEffect(Effect):
    name = "Vampirism"
    main_schema = {
        "hp": "Int",
    }
    effect_type = EffectType.Pure
    status = Status.Positive
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)

        if not source.is_damaged():
            return EffectResult.empty()

        hp_restored, n_resurrected = source.resurrect(self["hp"])

        if hp_restored <= 0:
            return EffectResult.empty()

        return EffectResult.event(
            VampirismAppliedEvent(
                stack_id=source.id,
                stack=source.name_count,
                hp=hp_restored,
                n_resurrected=n_resurrected,
            )
        )
