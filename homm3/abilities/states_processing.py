from homm3.abilities import Ability, register_ability
from homm3.contexts import StateApplicationContext
from homm3.enums import Status


@register_ability
class NegativeStatePurgeAbility(Ability):
    name = "NegativeStatePurge"

    def modify_state_application(self, ctx: StateApplicationContext, view):
        if ctx.stack_id != self.stack_id:
            return

        state = ctx.state
        if state.status != Status.Negative:
            return

        if state.rounds is None:
            return

        state.rounds = min(state.rounds, 1)