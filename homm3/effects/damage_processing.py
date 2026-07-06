from homm3.effects import Effect, EffectResult, register_effect
from homm3.effects.states_processing import ApplyStateEffect
from homm3.enums import Status, EffectType, EffectElement, SpellMastery


@register_effect
class InstantPhysicalDamageEffect(Effect):
    name = "InstantPhysicalDamage"
    main_schema = {
        "val": "Int",
    }
    effect_type = EffectType.Physical
    status = Status.Negative

    def apply(self, controller) -> EffectResult:
        damage = self["val"]
        return controller.apply_physical_damage(
            attacker_id=self.source_id,
            defender_id=self.target_id,
            damage=damage,
            damage_formula=f"{damage}",
        )


@register_effect
class InstantPhysicalDamagePerUnitEffect(Effect):
    name = "InstantPhysicalDamagePerUnit"
    main_schema = {
        "val": "Int",
    }
    effect_type = EffectType.Physical
    status = Status.Negative
    log_applying = True

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)
        damage = self["val"] * source.count
        return controller.apply_instant_damage(
            attacker_id=self.source_id,
            defender_id=self.target_id,
            damage=damage,
            damage_formula=f"{damage} = {self['val']} *{source.count}",
        )


@register_effect
class BlessEffect(ApplyStateEffect):
    name = "Bless"
    states = ("Blessed",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    level = 1
    element = EffectElement.Water

    def state_params(self, state_name: str) -> dict:
        bonus = {
            SpellMastery.No: 0,
            SpellMastery.Basic: 0,
            SpellMastery.Advanced: 1,
            SpellMastery.Expert: 1,
        }[self["mastery"]]
        return {"bonus": bonus, "rounds": self["rounds"]}


@register_effect
class CurseEffect(ApplyStateEffect):
    name = "Curse"
    states = ("Cursed",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Negative
    level = 1
    element = EffectElement.Fire

    def state_params(self, state_name: str) -> dict:
        penalty = {
            SpellMastery.No: 0,
            SpellMastery.Basic: 0,
            SpellMastery.Advanced: 1,
            SpellMastery.Expert: 1,
        }[self["mastery"]]
        return {"penalty": penalty, "rounds": self["rounds"]}


@register_effect
class AirShieldEffect(ApplyStateEffect):
    name = "AirShield"
    states = ("AirShield",)
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int",
    }
    effect_type = EffectType.Magical
    status = Status.Positive
    level = 3
    element = EffectElement.Air

    def state_params(self, state_name: str) -> dict:
        k = {
            SpellMastery.No: 0.25,
            SpellMastery.Basic: 0.25,
            SpellMastery.Advanced: 0.5,
            SpellMastery.Expert: 0.5,
        }[self["mastery"]]
        return {"factor": k, "rounds": self["rounds"]}
