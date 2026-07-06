from homm3.effects import register_effect, EffectResult
from homm3.effects.states_processing import ApplyStateEffect
from homm3.events.effects_processing import EffectBlockedEvent
from homm3.enums import Status, EffectDomain, EffectType, EffectElement, SpellMastery


@register_effect
class FreezeEffect(ApplyStateEffect):
    name = "Freeze"
    main_schema = {
        "rounds": "Int",
    }
    states = ("Frozen",)
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 4
    domains = (EffectDomain.Cold,)


@register_effect
class PetrificationEffect(ApplyStateEffect):
    name = "Petrification"
    states = ("Stoned",)
    main_schema = {
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 3


@register_effect
class ParalyzingVenomEffect(ApplyStateEffect):
    name = "ParalyzingVenom"
    states = ("Paralysed",)
    main_schema = {
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 4


@register_effect
class BlindEffect(ApplyStateEffect):
    name = "Blind"
    states = ("Blinded",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int|Str",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 2
    element = EffectElement.Fire
    domains = (EffectDomain.Mind,)
    cumulative = True


@register_effect
class BindEffect(ApplyStateEffect):
    name = "Bind"
    states = ("Binded",)
    effect_type = EffectType.Physical
    status = Status.Negative
    cumulative = False


@register_effect
class HypnotizeEffect(ApplyStateEffect):
    name = "Hypnotize"
    states = ("Hypnotized",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 3
    element = EffectElement.Air
    domains = (EffectDomain.Mind,)

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)
        target = controller.battle.id2stack(self.target_id)

        if target.has_state("Hypnotized"):
            return EffectResult.event(
                EffectBlockedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    effect=str(self),
                    reason="AlreadyApplied",
                )
            )

        p = {
            SpellMastery.No: 10,
            SpellMastery.Basic: 10,
            SpellMastery.Advanced: 20,
            SpellMastery.Expert: 50,
        }[self["mastery"]]
        power = source.count * 25 + p

        if power < target.health_all:
            return EffectResult.event(
                EffectBlockedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    effect=str(self),
                    reason="Power",
                )
            )

        if power < target.health_all:
            return EffectResult.empty()

        return super().apply(controller)

    def state_params(self, state_name: str) -> dict:
        return {"rounds": self["rounds"]}
