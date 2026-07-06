from homm3.states import State, register_state
from homm3.enums import Status
from homm3.effects import EffectResult
from homm3.contexts import PhysicalDamageContext, SpeedContext
from homm3.values import Term, Linear


@register_state
class AcidCorrosionState(State):
    name = "AcidCorrosion"
    main_schema = {
        "val": "Int",
    }
    cumulative = True
    dispellable = False
    status = Status.Negative

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stacks = 1

    def on_prolong(self, other: "State", controller) -> EffectResult:
        self.stacks += 1
        return EffectResult.empty()

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return
        penalty = -self["val"] * self.stacks
        label = self.name
        if self.stacks > 1:
            label += f" x{self.stacks}"
        ctx.defense["base"].add(Term(penalty, label=label))


@register_state
class StoneSkinState(State):
    name = "StoneSkin"
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Positive

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return
        ctx.defense["base"].add(Term(self["val"], label="StoneSkin"))


@register_state
class SlowState(State):
    name = "Slow"
    cancel = ("Haste",)
    main_schema = {
        "k": "Float",
        "b": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def modify_speed(self, ctx: SpeedContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.speed.apply(Linear(self["k"], self["b"], label="Slow"))


@register_state
class HasteState(State):
    name = "Haste"
    cancel = ("Slow",)
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Positive

    def modify_speed(self, ctx: SpeedContext, view):
        if ctx.stack_id != self.stack_id:
            return
        ctx.speed["base"].add(Term(self["val"], label="Haste"))


@register_state
class WeakenedState(State):
    name = "Weakened"
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        ctx.attack["base"].add(Term(-self["val"], label="Weakened"))


@register_state
class BloodlustState(State):
    name = "Bloodlust"
    main_schema = {
        "val": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Positive

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        ctx.attack["base"].add(Term(self["val"], label="BloodLust"))


@register_state
class DisruptingRayState(State):
    name = "DisruptingRay"
    main_schema = {
        "val": "Int",
    }
    cumulative = True
    dispellable = False
    status = Status.Negative

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stacks = 1

    def on_prolong(self, other: State, controller) -> EffectResult:
        self.stacks += 1
        return EffectResult.empty()

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return

        label = "DisruptingRay"
        if self.stacks > 1:
            label += f" x{self.stacks}"
        ctx.defense["base"].add(Term(-self["val"] * self.stacks, label=label))


@register_state
class DiseasedState(State):
    name = "Diseased"
    main_schema = {
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id == self.stack_id:
            ctx.attack["base"].add(Term(-2, label="Diseased"))

        if ctx.defender_id == self.stack_id:
            ctx.defense["base"].add(Term(-2, label="Diseased"))