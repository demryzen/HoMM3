from homm3.abilities import Ability, register_ability
from homm3.values import Term


@register_ability
class ImmunityAbility(Ability):
    name = "Immunity"
    main_schema = {
        "arg": "ImmunityArg",
    }


@register_ability
class ResistanceAbility(Ability):
    name = "Resistance"
    main_schema = {
        "arg": "ImmunityArg",
    }

    def modify_magical_damage(self, ctx, view):
        if ctx.defender_id != self.stack_id:
            return

        arg = self["arg"]
        if hasattr(arg, "matches"):
            matched = arg.matches(ctx.effect)
        else:
            matched = arg == ctx.effect.name

        if matched:
            ctx.damage["factor_prod"].mul(Term(0.5, label="Resistance"))


@register_ability
class VulnerabilityAbility(Ability):
    name = "Vulnerability"
    main_schema = {
        "arg": "ImmunityArg",
    }

    def modify_magical_damage(self, ctx, view):
        if ctx.defender_id != self.stack_id:
            return

        arg = self["arg"]
        if hasattr(arg, "matches"):
            matched = arg.matches(ctx.effect)
        else:
            matched = arg == ctx.effect.name

        if matched:
            ctx.damage["factor_prod"].mul(Term(2.0, label="Vulnerability"))


@register_ability
class SpellVulnerabilityAuraAbility(Ability):
    name = "SpellVulnerabilityAura"
    main_schema = {
        "probability": "Probability",
    }


@register_ability
class SpellResistanceAbility(Ability):
    name = "SpellResistance"
    main_schema = {
        "probability": "Probability",
    }


@register_ability
class SpellResistanceAuraAbility(Ability):
    name = "SpellResistanceAura"
    main_schema = {
        "probability": "Probability",
    }


@register_ability
class MagicMirrorAbility(Ability):
    name = "MagicMirror"
    main_schema = {
        "probability": "Probability",
    }


@register_ability
class SpellDamageReductionAbility(Ability):
    name = "SpellDamageReduction"
    main_schema = {
        "val": "Int",
    }

    def modify_magical_damage(self, ctx, view):
        if ctx.defender_id != self.stack_id:
            return
        ctx.damage["factor_prod"].mul(Term(1 - self["val"] / 100, label="SpellDamageReduction"))


@register_ability
class EyelessAbility(Ability):
    name = "Eyeless"
    origin = (
        "Immunity(Blind)",
        "Immunity(Petrification)",
    )