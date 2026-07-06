from homm3.strategies import MeleeStrategy
from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType


class RuneBasedStrategy(MeleeStrategy):
    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        if ctx.has(ActionType.Strike):
            return ctx.get(ActionType.Strike)

        if ctx.has(ActionType.MoveAndStrike):
            return ctx.get(ActionType.MoveAndStrike)

        stack = view.stack(ctx.stack_id)
        runes = stack.get_ability("PossessRunes")
        if runes is None:
            return super().choose_action(ctx, view)
        if (
                not self.is_vs_ranged(ctx, view) and
                not self.enemy_can_reach_in_1_move(ctx) and
                ctx.has(ActionType.Defense) and
                runes.level < runes["max_level"]
        ):
            return ctx.get(ActionType.Defense)

        return super().choose_action(ctx, view)
