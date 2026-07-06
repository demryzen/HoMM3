from homm3.effects.states_processing import ApplyStateEffect
from homm3.effects import register_effect
from homm3.enums import Status, EffectType, EffectElement, SpellMastery, UnitEntity
from homm3.filters import EntityFilter


@register_effect
class AcidCorrosionEffect(ApplyStateEffect):
    name = "AcidCorrosion"
    states = ("AcidCorrosion",)
    main_schema = {
        "val": "Int",
    }
    effect_type = EffectType.Physical
    status = Status.Negative


@register_effect
class StoneSkinEffect(ApplyStateEffect):
    name = "StoneSkin"
    states = ("StoneSkin",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    level = 1
    element = EffectElement.Earth

    def state_params(self, state_name: str) -> dict:
        val = {
            SpellMastery.No: 3,
            SpellMastery.Basic: 3,
            SpellMastery.Advanced: 6,
            SpellMastery.Expert: 6,
        }[self["mastery"]]
        return {"val": val, "rounds": self["rounds"]}


@register_effect
class SlowEffect(ApplyStateEffect):
    name = "Slow"
    states = ("Slow",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    element = EffectElement.Earth
    level = 1

    def state_params(self, state_name: str) -> dict:
        k, b = {
            SpellMastery.No: (0.75, 0),
            SpellMastery.Basic: (0.75, 0),
            SpellMastery.Advanced: (0.5, 1),
            SpellMastery.Expert: (0.5, 1),
        }[self["mastery"]]
        return {"k": k, "b": b, "rounds": self["rounds"]}


@register_effect
class HasteEffect(ApplyStateEffect):
    name = "Haste"
    states = ("Haste",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    element = EffectElement.Air
    level = 1

    def state_params(self, state_name: str) -> dict:
        val = {
            SpellMastery.No: 3,
            SpellMastery.Basic: 3,
            SpellMastery.Advanced: 5,
            SpellMastery.Expert: 5,
        }[self["mastery"]]
        return {"val": val, "rounds": self["rounds"]}


@register_effect
class WeaknessEffect(ApplyStateEffect):
    name = "Weakness"
    states = ("Weakened",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 2
    element = EffectElement.Water

    def state_params(self, state_name: str) -> dict:
        val = {
            SpellMastery.No: 3,
            SpellMastery.Basic: 3,
            SpellMastery.Advanced: 6,
            SpellMastery.Expert: 6,
        }[self["mastery"]]
        return {"val": val, "rounds": self["rounds"]}


@register_effect
class BloodlustEffect(ApplyStateEffect):
    name = "Bloodlust"
    states = ("Bloodlust",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    level = 1
    element = EffectElement.Fire

    def state_params(self, state_name: str) -> dict:
        val = {
            SpellMastery.No: 3,
            SpellMastery.Basic: 3,
            SpellMastery.Advanced: 6,
            SpellMastery.Expert: 6,
        }[self["mastery"]]
        return {"val": val, "rounds": self["rounds"]}


@register_effect
class DisruptingRayEffect(ApplyStateEffect):
    name = "DisruptingRay"
    states = ("DisruptingRay",)
    main_schema = {
        "mastery": "Mastery",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 2
    element = EffectElement.Air

    def state_params(self, state_name: str) -> dict:
        val = {
            SpellMastery.No: 3,
            SpellMastery.Basic: 3,
            SpellMastery.Advanced: 4,
            SpellMastery.Expert: 5,
        }[self["mastery"]]
        return {"val": val}


@register_effect
class DiseaseEffect(ApplyStateEffect):
    name = "Disease"
    states = ("Diseased",)
    main_schema = {
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    cumulative = True
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )