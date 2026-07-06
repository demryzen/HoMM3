from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType
from homm3.params import RANGE_PENALTY_DISTANCE


class Strategy:
    def __str__(self) -> str:
        return self.__class__.__name__

    def choose_actions(self, ctx: ActionContext, view: "BattleView") -> tuple[AvailableAction, list[AvailableAction]]:
        free_actions = self.choose_free_actions(ctx, view)
        regular_actions = [action for action in ctx.actions if not action.is_free]
        regular_ctx = ctx.copy_with_actions(regular_actions)
        return self.choose_action(regular_ctx, view), free_actions

    def choose_free_actions(self, ctx: ActionContext, view: "BattleView") -> list[AvailableAction]:
        return [action for action in ctx.actions if action.is_free]

    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        raise NotImplementedError

    @staticmethod
    def choose_first(ctx: ActionContext, *action_types: ActionType) -> AvailableAction:
        for action_type in action_types:
            action = ctx.get(action_type)
            if action is not None:
                return action
        if not ctx.actions:
            raise ValueError("No available actions")
        return ctx.actions[0]

    def move(self, ctx: ActionContext, steps: int | None = None) -> AvailableAction:
        action = ctx.get(ActionType.Move)
        if action is None:
            return self.choose_first(ctx, ActionType.Defense, ActionType.Wait)

        max_steps = action.params["steps"]
        if (steps is None) or (steps <= 0):
            steps = max_steps
        else:
            steps = min(steps, max_steps)

        return action.modify(steps=steps)

    def safe_move_against_enemy(self, ctx: ActionContext) -> AvailableAction:
        steps = ctx.distance - ctx.enemy_speed - 1
        return self.move(ctx, steps)

    def wait_or_move(self, ctx: ActionContext, steps: int | None = None) -> AvailableAction:
        if ctx.is_waited:
            return self.move(ctx, steps)
        return self.choose_first(ctx, ActionType.Wait, ActionType.Move, ActionType.Defense)

    def wait_or_defense(self, ctx: ActionContext) -> AvailableAction:
        if ctx.is_waited:
            return self.choose_first(ctx, ActionType.Defense)
        return self.choose_first(ctx, ActionType.Wait, ActionType.Defense)

    def wait_or_shoot(self, ctx: ActionContext) -> AvailableAction:
        if ctx.is_waited:
            return self.choose_first(ctx, ActionType.Shoot)
        return self.choose_first(ctx, ActionType.Wait, ActionType.Shoot)

    def can_reach_in_2_moves(self, ctx: ActionContext) -> bool:
        return 2 * ctx.stack_speed >= ctx.distance

    def is_vs_ranged(self, ctx: ActionContext, view: "BattleView") -> bool:
        return view.stack(ctx.enemy_id).shots > 0

    def is_vs_ranged_without_penalty(self, ctx: ActionContext, view: "BattleView") -> bool:
        enemy = view.stack(ctx.enemy_id)
        is_caster = str(enemy.strategy) == "FaerieSpellCasterStrategy"
        is_ranged = (enemy.is_ranged() > 0) and enemy.has_ability("NoRangePenalty")
        return is_caster or is_ranged

    def is_in_range_penalty_zone(self, ctx: ActionContext) -> bool:
        return ctx.distance <= RANGE_PENALTY_DISTANCE

    def is_vs_hit_and_run(self, ctx: ActionContext, view: "BattleView") -> bool:
        return view.stack(ctx.enemy_id).has_ability("HitAndRun")

    def is_vs_cavalry(self, ctx: ActionContext, view: "BattleView") -> bool:
        return view.stack(ctx.enemy_id).has_ability("JoustingBonus")

    def can_pass_range_penalty_zone_in_1_move(self, ctx: ActionContext) -> bool:
        return ctx.distance - ctx.stack_speed <= RANGE_PENALTY_DISTANCE

    def enemy_can_reach_in_1_move(self, ctx: ActionContext) -> bool:
        return ctx.enemy_speed >= ctx.distance

    def enemy_is_defending(self, ctx: ActionContext, view: "BattleView") -> bool:
        enemy = view.stack(ctx.enemy_id)
        return enemy.has_state("Defense")


class MeleeStrategy(Strategy):
    def go_closer_to_ranged(self, ctx: ActionContext) -> AvailableAction:
        if self.is_in_range_penalty_zone(ctx):
            return self.move(ctx)

        if self.can_pass_range_penalty_zone_in_1_move(ctx):
            steps = ctx.distance - RANGE_PENALTY_DISTANCE
            return self.move(ctx, steps)

        if self.can_reach_in_2_moves(ctx):
            if ctx.is_faster:
                return self.wait_or_move(ctx)
            return self.move(ctx)

        steps = ctx.distance - RANGE_PENALTY_DISTANCE
        return self.move(ctx, steps)

    def go_closer_to_hit_and_run(self, ctx: ActionContext) -> AvailableAction:
        if self.can_reach_in_2_moves(ctx) and ctx.is_faster:
            return self.wait_or_move(ctx)

        return self.move(ctx)

    def go_closer_to_cavalry(self, ctx: ActionContext) -> AvailableAction:
        if ctx.is_faster:
            if self.can_reach_in_2_moves(ctx):
                return self.wait_or_move(ctx)
            steps_safe = ctx.distance - ctx.enemy_speed - 1
            return self.move(ctx, steps_safe)

        can_enemy_reach_in_2 = 2 * ctx.enemy_speed >= ctx.distance
        if not can_enemy_reach_in_2:
            steps = ctx.distance - 2 * ctx.enemy_speed - 1
            return self.move(ctx, steps)

        steps_safe = ctx.distance - ctx.enemy_speed - 1
        steps_cut_runup = max(0, min(ctx.stack_speed, steps_safe))
        if steps_cut_runup >= 1:
            return self.move(ctx, steps_cut_runup)

        return self.choose_first(ctx, ActionType.Defense)

    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        if ctx.has(ActionType.Strike):
            return ctx.get(ActionType.Strike)

        if ctx.has(ActionType.MoveAndStrike):
            return ctx.get(ActionType.MoveAndStrike)

        if self.is_vs_ranged_without_penalty(ctx, view):
            return self.move(ctx, ctx.stack_speed)

        if self.is_vs_ranged(ctx, view):
            return self.go_closer_to_ranged(ctx)

        if self.is_vs_cavalry(ctx, view):
            return self.go_closer_to_cavalry(ctx)

        if self.is_vs_hit_and_run(ctx, view):
            return self.go_closer_to_hit_and_run(ctx)

        if not ctx.is_faster:
            if self.enemy_is_defending(ctx, view) and (ctx.distance > ctx.enemy_speed + 1):
                return self.safe_move_against_enemy(ctx)
            return self.choose_first(ctx, ActionType.Defense, ActionType.Wait, ActionType.Move)

        if self.can_reach_in_2_moves(ctx):
            return self.wait_or_move(ctx)

        steps = ctx.distance - ctx.enemy_speed - 1
        return self.move(ctx, steps)


class RangedStrategy(MeleeStrategy):
    def choose_action(self, ctx: ActionContext, view: "BattleView") -> AvailableAction:
        enemy = view.stack(ctx.enemy_id)
        # stack = view.stack(ctx.stack_id)
        # if enemy.has_ability("PreemptiveShot") and stack.has_ability("NoMeleePenalty"):
        #     return super().choose_action(ctx, view)

        if ctx.has(ActionType.Shoot):
            if (ctx.is_faster and not ctx.is_waited) and (ctx.enemy_speed < ctx.distance) and (not enemy.is_ranged()):
                return self.wait_or_shoot(ctx)
            return ctx.get(ActionType.Shoot)

        return super().choose_action(ctx, view)