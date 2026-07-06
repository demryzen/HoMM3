from homm3.contexts import ActionContext, PhysicalDamageContext
from homm3.enums import EventType, Status, ActionType, SpellMastery
from homm3.states import State, register_state, state_from_str
from homm3.values import Term
from homm3.effects import EffectResult


@register_state
class FrozenState(State):
    name = "Frozen"
    main_schema = {
        "rounds": "Int",
    }
    status = Status.Negative
    cumulative = True

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.clear("Frozen")

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return
        ctx.damage["factor_prod"].mul(Term(1.25, label="Frozen"))

    def on_event(self, event, controller):
        result = super().on_event(event, controller)
        if (event.type == EventType.DamageApplied) and (event.defender_id == self.stack_id):
            self.expire()
        return result


@register_state
class StonedState(State):
    name = "Stoned"
    main_schema = {
        "rounds": "Int",
    }
    status = Status.Negative
    cumulative = True

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.clear("Stoned")

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return
        ctx.damage["factor_prod"].mul(Term(0.5, label="Stoned"))

    def on_event(self, event, controller):
        result = super().on_event(event, controller)
        if (event.type == EventType.DamageApplied) and (event.defender_id == self.stack_id):
            self.expire()
        return result


@register_state
class ParalysedState(State):
    name = "Paralysed"
    main_schema = {
        "rounds": "Int",
    }
    status = Status.Negative
    cumulative = True

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.clear("Paralysed")

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if (event.type == EventType.DamageApplied) and (event.defender_id == self.stack_id):
            self.expire()
            result.extend(
                controller.add_state(
                    self.stack_id,
                    state_from_str("ParalysedRetaliation"),
                )
            )

        return result


@register_state
class ParalysedRetaliationState(State):
    name = "ParalysedRetaliation"
    status = Status.Negative
    dispellable = False
    cumulative = False

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        if not ctx.is_retaliation:
            return
        ctx.damage["factor_prod"].mul(Term(0.25, label="Paralysed"))

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if event.type == EventType.TurnEnded:
            self.expire()

        return result


@register_state
class BlindedState(State):
    name = "Blinded"
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int|Str",
    }
    status = Status.Negative
    cumulative = True

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.clear("Blinded")

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if (event.type == EventType.DamageApplied) and (event.defender_id == self.stack_id):
            self.expire()

            if self["mastery"] == SpellMastery.Expert:
                result.extend(
                    controller.add_state(
                        self.stack_id,
                        state_from_str("SkipRetaliation"),
                    )
                )
            else:
                result.extend(
                    controller.add_state(
                        self.stack_id,
                        state_from_str(
                            "BlindRetaliation",
                            params={"mastery": self["mastery"]},
                        ),
                    )
                )

        return result


@register_state
class BlindRetaliationState(State):
    name = "BlindRetaliation"
    main_schema = {
        "mastery": "Mastery",
    }
    status = Status.Negative
    dispellable = False
    cumulative = False

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        if not ctx.is_retaliation:
            return

        match self["mastery"]:
            case SpellMastery.Basic:
                ctx.damage["factor_prod"].mul(Term(0.5, label="Blind retaliation"))
            case SpellMastery.Advanced:
                ctx.damage["factor_prod"].mul(Term(0.25, label="Blind retaliation"))

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if event.type == EventType.TurnEnded:
            self.expire()

        return result


@register_state
class BindedState(State):
    name = "Binded"
    status = Status.Negative
    cumulative = False

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return

        ctx.remove(ActionType.Move, reason="Binded")
        ctx.remove(ActionType.MoveAndStrike, reason="Binded")

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if (event.type == EventType.StackMoved) and (event.stack_id == self.source_id):
            self.expire()

        if (event.type == EventType.StackDied) and (event.stack_id == self.source_id):
            self.expire()

        return result


@register_state
class SkipRetaliationState(State):
    name = "SkipRetaliation"
    status = Status.Negative
    dispellable = False
    cumulative = False

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if event.type == EventType.TurnEnded:
            self.expire()

        return result


@register_state
class HypnotizedState(State):
    name = "Hypnotized"
    main_schema = {
        "rounds": "Int",
    }
    status = Status.Negative
    cumulative = False

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.stack_id != self.stack_id:
            return
        defense = ctx.get(ActionType.Defense)
        ctx.actions.clear()
        if defense is not None:
            ctx.actions.append(defense)


@register_state
class MeditatingState(State):
    name = "Meditating"
    status = Status.Positive
    dispellable = False
    cumulative = False

    def modify_actions(self, ctx: ActionContext, view):
        if ctx.enemy_id != self.stack_id:
            return
        ctx.remove_target(self.stack_id, reason="Meditation")

    def on_event(self, event, controller) -> EffectResult:
        result = super().on_event(event, controller)
        if (event.type == EventType.TurnStarted) and (event.stack_id == self.stack_id):
            self.expire()
        return result
