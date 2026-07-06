import numpy as np

from homm3.abilities import Ability, register_ability
from homm3.effects import Effect
from homm3.enums import EffectType, EffectDomain
from homm3.values import Term, Floor


@register_ability
class NoMeleePenaltyAbility(Ability):
    name = "NoMeleePenalty"


@register_ability
class NoRangePenaltyAbility(Ability):
    name = "NoRangePenalty"


@register_ability
class NoObstaclePenaltyAbility(Ability):
    name = "NoObstaclePenalty"


@register_ability
class IgnoreDefenseAbility(Ability):
    name = "IgnoreDefense"
    main_schema = {
        "attack": "AttackType",
        "val": "Int",
    }
    priority = 10

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return
        if ctx.attack_type != self["attack"]:
            return
        ctx.defense["factors"].mul(Term(1 - self["val"] / 100, label=None))
        ctx.defense.apply(Floor(label=None))
        ctx.defense.add(Term(-1, label="IgnoreDefense"))


@register_ability
class IgnoreAttackAbility(Ability):
    name = "IgnoreAttack"
    main_schema = {
        "val": "Int",
    }
    priority = 10

    def modify_physical_damage(self, ctx, view):
        if ctx.defender_id != self.stack_id:
            return
        ctx.attack["factors"].mul(Term(1 - self["val"] / 100, label=None))


@register_ability
class RevengeAbility(Ability):
    name = "Revenge"

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return

        source = view.stack(self.stack_id)
        health_all = source.health_all
        modifier = np.sqrt((source.count_base + 1) * source.health_max / (health_all + source.health_max) - 1)
        if modifier > 1e-5:
            ctx.damage["factor_sum"].add(Term(modifier, label="Revenge"))


@register_ability
class MagicAttackAbility(Ability):
    name = "MagicAttack"

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return
        target = view.stack(ctx.defender_id)
        if not self.target_has_full_magic_immunity(target):
            return
        ctx.damage["factor_prod"].mul(Term(0.5, label="MagicAttack"))

    @staticmethod
    def target_has_full_magic_immunity(target) -> bool:
        for level in (1, 2, 3, 4, 5):
            effect = Effect()
            effect.effect_type = EffectType.Magical
            effect.level = level
            if not target.is_immune_to_effect(effect):
                return False
        return True


@register_ability
class PsychicAttackAbility(Ability):
    name = "PsychicAttack"

    @staticmethod
    def target_has_mind_immunity(target) -> bool:
        effect = Effect()
        effect.effect_type = EffectType.Magical
        effect.domains = (EffectDomain.Mind,)
        return target.is_immune_to_effect(effect)

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return
        target = view.stack(ctx.defender_id)
        if not self.target_has_mind_immunity(target):
            return
        ctx.damage["factor_prod"].mul(Term(0.5, label="PsychicAttack"))


@register_ability
class OppositeAbility(Ability):
    name = "Opposite"
    main_schema = {
        "target": "Str",
    }

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return

        target = view.stack(ctx.defender_id)
        if target.name != self["target"]:
            return

        ctx.damage["factor_sum"].add(Term(1.0, label=f"Opposite {target.name}"))


@register_ability
class HatesAbility(Ability):
    name = "Hates"
    main_schema = {
        "target": "Str",
    }

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return

        target = view.stack(ctx.defender_id)
        if target.name != self["target"]:
            return

        ctx.damage["factor_sum"].add(Term(0.5, label=f"Hates {target.name}"))


@register_ability
class DeathBlowAbility(Ability):
    name = "DeathBlow"
    main_schema = {
        "probability": "Probability",
    }

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return

        if ctx.rng is None:
            return

        if ctx.rng.random() < self["probability"]:
            ctx.damage["factor_prod"].mul(Term(2.0, label="DeathBlow"))


@register_ability
class JoustingBonusAbility(Ability):
    name = "JoustingBonus"
    main_schema = {
        "val": "Int",
    }

    def modify_physical_damage(self, ctx, view):
        if ctx.attacker_id != self.stack_id:
            return

        source = view.stack(ctx.attacker_id)
        if source.run_up <= 0:
            return

        target = view.stack(ctx.defender_id)
        if target.is_immune_to_ability(self.name):
            return

        bonus = self["val"] * source.run_up / 100
        ctx.damage["factor_sum"].add(Term(bonus, label="JoustingBonus"))