from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType
from homm3.params import RANGE_PENALTY_DISTANCE
from homm3.strategies import MeleeStrategy


class CavalryStrategy(MeleeStrategy):
    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        if ctx.has(ActionType.Strike):
            return ctx.get(ActionType.Strike)

        if ctx.has(ActionType.MoveAndStrike):
            return ctx.get(ActionType.MoveAndStrike)

        if self.is_vs_ranged(ctx, view):
            return self.next_action_vs_ranged(ctx)

        if self.is_vs_hit_and_run(ctx, view):
            return self.go_closer_to_hit_and_run(ctx)

        return self.next_action_vs_melee(ctx)

    def next_action_vs_ranged(self, ctx: ActionContext) -> AvailableAction:
        steps_jousting = ctx.distance - ctx.stack_speed

        if self.is_in_range_penalty_zone(ctx):
            return self.move(ctx, steps_jousting)

        if self.can_reach_in_2_moves(ctx):
            if ctx.is_faster:
                return self.wait_or_move(ctx, steps_jousting)

            if self.can_pass_range_penalty_zone_in_1_move(ctx):
                steps = min(ctx.distance - RANGE_PENALTY_DISTANCE, steps_jousting)
            else:
                steps = steps_jousting
            return self.move(ctx, steps)

        return self.move(ctx, steps_jousting)

    def next_action_vs_melee(self, ctx: ActionContext) -> AvailableAction:
        if not ctx.is_faster:
            return self.choose_first(ctx, ActionType.Defense)

        if self.can_reach_in_2_moves(ctx):
            steps = ctx.distance - ctx.stack_speed
            return self.wait_or_move(ctx, steps)

        steps = ctx.distance - ctx.enemy_speed - 1
        return self.move(ctx, steps)
