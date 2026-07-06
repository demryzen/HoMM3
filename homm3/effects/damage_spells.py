from homm3.effects import Effect, register_effect
from homm3.enums import Status, EffectType, EffectElement, EffectDomain, SpellMastery


class DamageSpellEffect(Effect):
    effect_type = EffectType.Magical
    status = Status.Negative
    log_applying = True

    def base_damage(self, source):
        raise NotImplementedError

    def apply(self, controller):
        source = None if self.source_id is None else controller.battle.id2stack(self.source_id)
        return controller.apply_magical_damage(
            attacker_id=self.source_id,
            defender_id=self.target_id,
            effect=self,
            damage=self.base_damage(source),
        )


@register_effect
class MagicArrowSpell(DamageSpellEffect):
    name = "MagicArrow"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 1
    element = EffectElement.No

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 10,
            SpellMastery.Basic: 10,
            SpellMastery.Advanced: 20,
            SpellMastery.Expert: 30,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 10 * self["power"] + additional_damage


@register_effect
class MeteorShowerSpell(DamageSpellEffect):
    name = "MeteorShower"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 4
    element = EffectElement.Earth

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 25,
            SpellMastery.Basic: 25,
            SpellMastery.Advanced: 50,
            SpellMastery.Expert: 100,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 25 * self["power"] + additional_damage


@register_effect
class IceBoltSpell(DamageSpellEffect):
    name = "IceBolt"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 2
    element = EffectElement.Water
    domains = (EffectDomain.Cold,)

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 10,
            SpellMastery.Basic: 10,
            SpellMastery.Advanced: 20,
            SpellMastery.Expert: 50,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 20 * self["power"] + additional_damage


@register_effect
class FrostRingSpell(DamageSpellEffect):
    name = "FrostRing"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 3
    element = EffectElement.Water
    domains = (EffectDomain.Cold,)

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 15,
            SpellMastery.Basic: 15,
            SpellMastery.Advanced: 30,
            SpellMastery.Expert: 60,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 10 * self["power"] + additional_damage


@register_effect
class FireBallSpell(DamageSpellEffect):
    name = "FireBall"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 3
    element = EffectElement.Fire

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 15,
            SpellMastery.Basic: 15,
            SpellMastery.Advanced: 30,
            SpellMastery.Expert: 60,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 10 * self["power"] + additional_damage


@register_effect
class InfernoSpell(DamageSpellEffect):
    name = "Inferno"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 4
    element = EffectElement.Fire

    def base_damage(self, source) -> int:
        mastery = self["mastery"]
        additional_damage = {
            SpellMastery.No: 20,
            SpellMastery.Basic: 20,
            SpellMastery.Advanced: 40,
            SpellMastery.Expert: 80,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mastery}'!")

        return 10 * self["power"] + additional_damage


@register_effect
class LightningBoltSpell(DamageSpellEffect):
    name = "LightningBolt"
    main_schema = {
        "mode": "Str",
        "power": "Int",
    }
    level = 2
    element = EffectElement.Air

    def base_damage(self, source) -> int:
        mode = self["mode"]

        if mode == "Creature":
            return source.count * self["power"]

        mastery = SpellMastery.from_str(mode)
        additional_damage = {
            SpellMastery.No: 10,
            SpellMastery.Basic: 10,
            SpellMastery.Advanced: 20,
            SpellMastery.Expert: 50,
        }.get(mastery)

        if additional_damage is None:
            raise ValueError(f"Unknown mastery level '{mode}'!")

        return 25 * self["power"] + additional_damage


@register_effect
class ArmageddonSpell(DamageSpellEffect):
    name = "Armageddon"
    main_schema = {
        "mastery": "Mastery",
        "power": "Int",
    }
    level = 4
    element = EffectElement.Fire

    def base_damage(self, source) -> int:
        additional_damage = {
            SpellMastery.No: 30,
            SpellMastery.Basic: 30,
            SpellMastery.Advanced: 60,
            SpellMastery.Expert: 120,
        }[self["mastery"]]

        return 40 * self["power"] + additional_damage


@register_effect
class FireShieldDamageEffect(DamageSpellEffect):
    name = "FireShieldDamage"
    main_schema = {
        "damage": "Int",
    }
    element = EffectElement.Fire
    level = 4
    ignore_spell_resistance = False
    ignore_spell_level_immunity = True
    log_applying = True

    def base_damage(self, source) -> int:
        return self["damage"]