from homm3.effects import Effect, EffectResult, register_effect, effect_from_str
from homm3.effects.default_actions import AttackEffect
from homm3.effects.states_processing import ApplyStateEffect
from homm3.enums import AttackOrder, AttackType, Status


@register_effect
class HeatStrokeEffect(AttackEffect):
    name = "HeatStroke"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_attack(
            attacker_id=self.attacker_id,
            defender_id=self.defender_id,
            attack_type=AttackType.Special,
            attack_name="uses HeatStroke on",
            attack_order=AttackOrder.Regular,
        )


@register_effect
class MeditationEffect(ApplyStateEffect):
    name = "Meditation"
    states = ("Meditating",)
    status = Status.Positive
    log_applying = True


@register_effect
class ReturnEffect(Effect):
    name = "Return"
    main_schema = {
        "steps": "Int",
    }

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_return(
            stack_id=self.source_id,
            steps=self["steps"],
        )


@register_effect
class HitAndRunEffect(Effect):
    name = "HitAndRun"
    main_schema = {
        "steps": "Int",
        "speed": "Value",
    }

    def apply(self, controller: "BattleController") -> EffectResult:
        move_and_strike = effect_from_str(
            "MoveAndStrike",
            params={
                "steps": self["steps"],
                "speed": self["speed"],
            },
        ).bind(source_id=self.source_id, target_id=self.target_id)

        return_back = effect_from_str(
            "Return",
            params={
                "steps": self["steps"],
            },
        ).bind(source_id=self.source_id, target_id=self.source_id)

        return EffectResult(effects=[move_and_strike, return_back])

