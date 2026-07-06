from homm3.abilities import Ability, register_ability
from homm3.contexts import SpeedContext
from homm3.enums import UnitMovement
from homm3.values import Term


@register_ability
class FlyerSpeedPenaltyAbility(Ability):
    name = "FlyerSpeedPenalty"
    main_schema = {
        "val": "Int",
    }

    def modify_speed(self, ctx: SpeedContext, view):
        if self.stack_id is None:
            return

        if ctx.stack_id not in view.enemies_of(self.stack_id):
            return

        stack = view.stack(ctx.stack_id)
        if stack.unit.movement != UnitMovement.Flying:
            return

        ctx.speed["base"].add(Term(-self["val"], label=self.name))
