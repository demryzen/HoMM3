from homm3.effects import Effect, EffectResult, register_effect, effect_from_str
from homm3.enums import AttackOrder


@register_effect
class MoveEffect(Effect):
    name = "Move"
    main_schema = {
        "steps": "Int",
    }
    secondary_schema = {
        "speed": "Value",
    }

    @property
    def stack_id(self) -> str:
        return self.target_id

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_move(stack_id=self.stack_id, speed=self["speed"], steps=self["steps"])


class AttackEffect(Effect):
    name = "Attack"
    secondary_schema = {
        "attack_order": "AttackOrder",
        "additional_left": "Int",
    }
    default_params = {
        "attack_order": AttackOrder.Regular,
        "additional_left": 0,
    }

    @property
    def attacker_id(self) -> str:
        return self.source_id

    @property
    def defender_id(self) -> str:
        return self.target_id


@register_effect
class StrikeEffect(AttackEffect):
    name = "Strike"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_strike(
            attacker_id=self.attacker_id,
            defender_id=self.defender_id,
            attack_order=self["attack_order"],
            additional_left=self["additional_left"],
        )


@register_effect
class ShootEffect(AttackEffect):
    name = "Shoot"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_shoot(
            shooter_id=self.attacker_id,
            target_id=self.defender_id,
            attack_order=self["attack_order"],
            additional_left=self["additional_left"],
        )


@register_effect
class MoveAndStrikeEffect(Effect):
    name = "MoveAndStrike"
    main_schema = {
        "steps": "Int"
    }
    secondary_schema = {
        "speed": "Value"
    }

    def apply(self, controller: "BattleController") -> EffectResult:
        move_params = {
            "steps": self["steps"],
            "speed": self["speed"],
        }
        move_effect = effect_from_str("Move", params=move_params).bind(target_id=self.source_id)

        strike_params = {
            "attack_order": AttackOrder.Regular,
        }
        strike_effect = effect_from_str("Strike", params=strike_params).bind(source_id=self.source_id, target_id=self.target_id)

        return EffectResult(effects=[move_effect, strike_effect])


@register_effect
class DefenseEffect(Effect):
    name = "Defense"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_defense(stack_id=self.target_id)


@register_effect
class WaitEffect(Effect):
    name = "Wait"

    def apply(self, controller: "BattleController") -> EffectResult:
        return controller.perform_wait(stack_id=self.target_id)
