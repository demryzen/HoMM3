from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType
from homm3.strategies import MeleeStrategy


class HeatStrokeStrategy(MeleeStrategy):
    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        heat_stroke = ctx.get(ActionType.UseAbility)

        if (ctx.distance == 0) and (heat_stroke is not None):
            return heat_stroke

        if (ctx.distance == 1) and (heat_stroke is not None):
            if self.is_vs_ranged(ctx, view) and ctx.has(ActionType.MoveAndStrike):
                return ctx.get(ActionType.MoveAndStrike)
            return heat_stroke

        if ctx.has(ActionType.MoveAndStrike):
            return ctx.get(ActionType.MoveAndStrike)

        return super().choose_action(ctx, view)


class MeditationStrategy(MeleeStrategy):
    def choose_free_actions(self, ctx: ActionContext, view: "BattleView") -> list[AvailableAction]:
        return [action for action in ctx.actions if action.is_free and (action.effect == "Meditation")]

    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        meditation = next(
            (
                action
                for action in ctx.actions
                if not action.is_free and action.effect == "Meditation"
            ),
            None,
        )
        if meditation is not None:
            return meditation

        return super().choose_action(ctx, view)


class HitAndRunStrategy(MeleeStrategy):
    def hit_and_run(self, ctx: ActionContext) -> AvailableAction | None:
        for action in ctx.actions:
            if action.type == ActionType.UseAbility and action.effect == "HitAndRun":
                return action
        return None

    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        hit_and_run = self.hit_and_run(ctx)

        if self.is_vs_ranged(ctx, view):
            if ctx.has(ActionType.Strike):
                return ctx.get(ActionType.Strike)
            if ctx.has(ActionType.MoveAndStrike):
                return ctx.get(ActionType.MoveAndStrike)
            return self.go_closer_to_ranged(ctx)

        if self.is_vs_hit_and_run(ctx, view):
            if ctx.has(ActionType.Strike):
                return ctx.get(ActionType.Strike)

            stack = view.stack(ctx.stack_id)
            if hit_and_run is not None and stack.has_ability("IgnoreRetaliation"):
                return hit_and_run

            if ctx.is_faster:
                return self.wait_or_move(ctx)

            return self.move(ctx)

        if ctx.has(ActionType.Strike):
            return ctx.get(ActionType.Strike)

        if hit_and_run is not None:
            return hit_and_run

        if not ctx.is_faster:
            return self.choose_first(ctx, ActionType.Defense, ActionType.Wait, ActionType.Move)

        steps = ctx.distance - ctx.stack_speed
        return self.wait_or_move(ctx, steps=steps)