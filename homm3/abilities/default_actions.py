from homm3.abilities import Ability, register_ability
from homm3.contexts import DefenseActionContext
from homm3.values import Term


@register_ability
class EnhancedDefenseAbility(Ability):
    name = "EnhancedDefense"

    def modify_defense_action(self, ctx: DefenseActionContext, view: "BattleView"):
        if ctx.stack_id != self.stack_id:
            return
        ctx.val["base"].add(Term(80, label=self.name))
