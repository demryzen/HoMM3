from homm3.abilities import Ability, register_ability
from homm3.values import Term


@register_ability
class GoodMoraleAbility(Ability):
    name = "GoodMorale"
    priority = 10

    def modify_morale(self, ctx, view):
        if ctx.stack_id != self.stack_id:
            return

        stack = view.stack(self.stack_id)
        if not stack.is_affected_by_morale():
            return

        morale = ctx.morale.total()
        if morale < 1:
            ctx.morale.add(Term(1 - morale, label="GoodMorale"))


@register_ability
class DreadfulAbility(Ability):
    name = "Dreadful"
    main_schema = {
        "val": "Int",
    }

    def modify_morale(self, ctx, view):
        if ctx.enemy_id != self.stack_id:
            return

        stack = view.stack(ctx.stack_id)
        if not stack.is_affected_by_morale():
            return

        ctx.morale.add(Term(-self["val"], label="Dreadful"))


@register_ability
class InspiringAbility(Ability):
    name = "Inspiring"
    main_schema = {
        "val": "Int",
    }

    def modify_morale(self, ctx, view):
        if ctx.stack_id != self.stack_id:
            return

        stack = view.stack(ctx.stack_id)
        if not stack.is_affected_by_morale():
            return

        ctx.morale.add(Term(self["val"], label="Inspiring"))
