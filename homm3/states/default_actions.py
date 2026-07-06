from homm3.contexts import PhysicalDamageContext
from homm3.states import State, register_state
from homm3.values import Term
from homm3.enums import EventType


@register_state
class DefenseState(State):
    name = "Defense"
    main_schema = {
        "val": "Int"
    }
    cumulative = False
    dispellable = False

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view: "BattleView"):
        if ctx.defender_id != self.stack_id:
            return

        bonus = int(max(1, ctx.defense.total() * self["val"] / 100))
        ctx.defense["base"].add(Term(bonus, label="Defense action"))

    def on_event(self, event, controller):
        result = super().on_event(event, controller)

        if (event.type == EventType.TurnStarted) and (event.stack_id == self.stack_id):
            self.expire()

        return result