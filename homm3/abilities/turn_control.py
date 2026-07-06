from homm3.abilities import Ability, register_ability
from homm3.contexts import ActionContext
from homm3.enums import UnitEntity


@register_ability
class FearAbility(Ability):
    name = "Fear"
    main_schema = {
        "probability": "Probability",
    }

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id == self.stack_id:
            return

        if ctx.stack_id not in view.enemies_of(self.stack_id):
            return

        stack = view.stack(ctx.stack_id)
        if stack.unit.entity != UnitEntity.Living:
            return

        if stack.is_immune_to_ability("Fear"):
            return

        if ctx.rng.random() >= self["probability"]:
            return

        ctx.clear("Fear")
