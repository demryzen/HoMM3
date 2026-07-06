from homm3.effects import register_effect
from homm3.effects.states_processing import ApplyStateEffect
from homm3.enums import Status, EffectType, EffectElement


@register_effect
class FireShieldEffect(ApplyStateEffect):
    name = "FireShield"
    states = ("FireShield",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int|Str",
    }
    status = Status.Positive
    effect_type = EffectType.Magical
    level = 4
    element = EffectElement.Fire
    cumulative = True
