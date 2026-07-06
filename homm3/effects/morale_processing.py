from homm3.effects import Effect, EffectResult, register_effect


@register_effect
class GoodMoraleEffect(Effect):
    name = "GoodMorale"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.apply_good_morale(stack_id=self.target_id)


@register_effect
class BadMoraleEffect(Effect):
    name = "BadMorale"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.apply_bad_morale(stack_id=self.target_id)
