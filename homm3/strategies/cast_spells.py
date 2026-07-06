from homm3.strategies import MeleeStrategy
from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType


class FaerieSpellCasterStrategy(MeleeStrategy):
    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        action = ctx.get(ActionType.UseAbility)
        if action is not None:
            return action
        return super().choose_action(ctx, view)
