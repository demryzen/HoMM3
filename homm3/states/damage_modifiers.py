from homm3.contexts import BaseDamageContext, PhysicalDamageContext
from homm3.enums import Status, AttackType
from homm3.states import State, register_state
from homm3.values import Term


@register_state
class BlessedState(State):
    name = "Blessed"
    cancel = ("Cursed",)
    main_schema = {
        "bonus": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Positive

    def modify_base_damage(self, ctx: BaseDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        ctx.use_max(bonus=self["bonus"], reason="Blessed")


@register_state
class CursedState(State):
    name = "Cursed"
    cancel = ("Blessed",)
    main_schema = {
        "penalty": "Int",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Negative

    def modify_base_damage(self, ctx: BaseDamageContext, view):
        if ctx.attacker_id != self.stack_id:
            return
        ctx.use_min(penalty=self["penalty"], reason="Cursed")


@register_state
class AirShieldState(State):
    name = "AirShield"
    main_schema = {
        "factor": "Float",
        "rounds": "Int",
    }
    cumulative = True
    status = Status.Positive

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.defender_id != self.stack_id:
            return
        if ctx.attack_type != AttackType.Ranged:
            return
        ctx.damage["factor_prod"].mul(Term(1 - self["factor"], label="AirShield"))
