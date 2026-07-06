from homm3.abilities import Ability, register_ability
from homm3.contexts import ActionContext, AvailableAction
from homm3.enums import ActionType
from homm3.effects import effect_from_str


@register_ability
class CastAbility(Ability):
    name = "Cast"
    main_schema = {
        "spell": "Str",
        "val": "Int|Str",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used = 0

    def can_cast(self) -> bool:
        return self["val"] == "Inf" or self.used < self["val"]

    def mark_used(self):
        self.used += 1

    def modify_actions(self, ctx, view):
        if ctx.stack_id != self.stack_id:
            return
        if not self.can_cast():
            return

        ctx.add(
            AvailableAction(
                type=ActionType.UseAbility,
                source_id=ctx.stack_id,
                target_id=ctx.enemy_id,
                effect=self["spell"],
                ability=self,
            )
        )


@register_ability
class HeatStrokeAbility(Ability):
    name = "HeatStroke"

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return

        if ctx.distance > 1:
            return

        ctx.add(
            AvailableAction(
                type=ActionType.UseAbility,
                source_id=ctx.stack_id,
                target_id=ctx.enemy_id,
                effect="HeatStroke",
                ability=self,
            )
        )


@register_ability
class MeditationAbility(Ability):
    name = "Meditation"
    main_schema = {
        "mode": "Str",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used = False

    def can_activate(self) -> bool:
        return not self.used

    def mark_used(self):
        self.used = True

    def create_effect(self):
        return effect_from_str("Meditation").bind(
            source_id=self.stack_id,
            target_id=self.stack_id,
        )

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return

        if not self.can_activate():
            return

        if self["mode"] not in {"Free", "Action"}:
            raise ValueError(f"Unknown Meditation mode: {self['mode']}")

        ctx.add(
            AvailableAction(
                type=ActionType.UseAbility,
                source_id=ctx.stack_id,
                target_id=ctx.stack_id,
                effect="Meditation",
                ability=self,
                is_free=self["mode"] == "Free",
            )
        )


@register_ability
class HitAndRunAbility(Ability):
    name = "HitAndRun"

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return

        move_and_strike = ctx.get(ActionType.MoveAndStrike)
        if move_and_strike is None:
            return

        ctx.add(
            AvailableAction(
                type=ActionType.UseAbility,
                source_id=ctx.stack_id,
                target_id=ctx.enemy_id,
                effect="HitAndRun",
                ability=self,
                params=move_and_strike.params.copy(),
            )
        )

@register_ability
class SummonAbility(Ability):
    name = "Summon"
    main_schema = {
        "unit": "Str",
        "val": "Int",
    }
