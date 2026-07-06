import numpy as np

from homm3.effects import Effect, EffectResult, effect_from_str, register_effect
from homm3.events.cast_spells import RandomFaerieDragonSpellCastEvent
from homm3.enums import SpellMastery


@register_effect
class FaerieRandomSpellEffect(Effect):
    name = "FaerieRandomSpell"

    spells = {
        "MagicArrow": 10,
        "MeteorShower": 5,
        "IceBolt": 22,
        "FrostRing": 10,
        "FireBall": 21,
        "Inferno": 5,
        "LightningBolt": 22,
    }

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)
        target = controller.battle.id2stack(self.target_id)

        names = list(self.spells)
        weights = np.array([self.spells[name] for name in names], dtype=float)
        probabilities = weights / weights.sum()
        chosen = controller.battle.rng.choice(names, p=probabilities)
        effect = effect_from_str(chosen, params={"mastery": SpellMastery.Advanced, "power": 5 * source.count})

        return EffectResult(
            events=[
                RandomFaerieDragonSpellCastEvent(
                    stack_id=source.id,
                    stack=source.name_count,
                    spell=chosen,
                )
            ],
            effects=[effect.bind(source_id=source.id,target_id=target.id)],
        )


@register_effect
class EnchanterSpellsEffect(Effect):
    name = "EnchanterSpells"

    spells = {
        "StoneSkin": 15,
        "Slow": 10,
        "Weakness": 4,
        "Bless": 15,
        "Cure": 10,
        "Bloodlust": 5,
        "Haste": 15,
        "AirShield": 10,
    }

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)
        target = controller.battle.id2stack(self.target_id)

        available = []

        if not source.has_state("StoneSkin"):
            available.append("StoneSkin")
        if not source.has_state("Blessed"):
            available.append("Bless")
        if not source.has_state("Bloodlust"):
            available.append("Bloodlust")
        if not source.has_state("Haste"):
            available.append("Haste")
        if not source.has_state("AirShield") and target.is_ranged() and (controller.battle.distance > 0):
            available.append("AirShield")
        if not target.has_state("Slow"):
            available.append("Slow")
        if not target.has_state("Weakened"):
            available.append("Weakness")
        if source.health < source.health_base:
            available.append("Cure")

        if not available:
            return EffectResult.empty()

        weights = np.array([self.spells[name] for name in available], dtype=float)
        probabilities = weights / weights.sum()
        chosen = controller.battle.rng.choice(available, p=probabilities)

        spell_target_id = target.id if chosen in {"Slow", "Weakness"} else source.id

        params = {"mastery": SpellMastery.Expert, "rounds": 3}
        if chosen == "Cure":
            params = {"mastery": SpellMastery.Expert, "power": 3}

        effect = effect_from_str(chosen, params=params).bind(
            source_id=source.id,
            target_id=spell_target_id,
        )

        return EffectResult.effect(effect)


@register_effect
class SeaWitchSpellsEffect(Effect):
    name = "SeaWitchSpells"
    main_schema = {
        "mastery": "Mastery",
    }
    log_applying = False

    def apply(self, controller) -> EffectResult:
        target = controller.battle.id2stack(self.target_id)
        mastery = self["mastery"]

        if target.has_state("Weakened"):
            effect = effect_from_str(
                "DisruptingRay",
                params={"mastery": mastery},
            )
        else:
            effect = effect_from_str(
                "Weakness",
                params={"mastery": mastery, "rounds": 3},
            )

        return EffectResult.effect(
            effect.bind(source_id=self.source_id, target_id=self.target_id)
        )
