from homm3.abilities import Ability, register_ability
from homm3.contexts import PhysicalDamageContext
from homm3.values import Term


@register_ability
class DoubleLuckAbility(Ability):
    name = "DoubleLuck"

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        ctx.luck_coeff *= 2


@register_ability
class GoodLuckAbility(Ability):
    name = "GoodLuck"
    priority = 10

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        luck = ctx.luck.total()
        if luck < 1:
            ctx.luck.add(Term(1 - luck, label="GoodLuck"))


@register_ability
class BadLuckAbility(Ability):
    name = "BadLuck"
    main_schema = {
        "val": "Int",
    }

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return

        ctx.luck.add(Term(-self["val"], label="BadLuck"))
