from homm3.abilities import Ability, register_ability
from homm3.effects import EffectResult, effect_from_str
from homm3.enums import EventType, ActionType


@register_ability
class BreathAbility(Ability):
    name = "Breath"
    main_schema = {
        "distance": "Int",
    }


@register_ability
class UnblockableAbility(Ability):
    name = "Unblockable"


@register_ability
class RetaliationsAbility(Ability):
    name = "Retaliations"
    main_schema = {
        "val": "Int|Str",
    }


@register_ability
class IgnoreRetaliationAbility(Ability):
    name = "IgnoreRetaliation"


@register_ability
class MultipleStrikeAbility(Ability):
    name = "MultipleStrike"
    main_schema = {
        "val": "Int",
    }


@register_ability
class MultipleShootAbility(Ability):
    name = "MultipleShoot"
    main_schema = {
        "val": "Int",
    }


@register_ability
class PreemptiveShotAbility(Ability):
    name = "PreemptiveShot"
    main_schema = {
        "val": "Int|Str",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shots_done = 0

    def can_preemptive_shoot(self) -> bool:
        val = self["val"]

        if val == "Inf":
            return True

        if isinstance(val, int):
            return self.shots_done < val

        raise ValueError(f"Invalid PreemptiveShot value: {val}")

    def mark_used(self):
        self.shots_done += 1

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.ActionSelected:
            return EffectResult.empty()

        if event.action != ActionType.Shoot:
            return EffectResult.empty()

        if event.target_id != self.stack_id:
            return EffectResult.empty()

        if not self.can_preemptive_shoot():
            return EffectResult.empty()

        shooter = controller.battle.id2stack(self.stack_id)
        target = controller.battle.id2stack(event.stack_id)

        if shooter.is_died() or target.is_died():
            return EffectResult.empty()

        if shooter.shots <= 0:
            return EffectResult.empty()

        self.mark_used()

        return EffectResult.effect(
            effect_from_str(
                "Shoot",
                params={
                    "is_retaliation": False,
                    "is_preemptive": True,
                    "is_additional": False,
                    "additional_left": 0,
                },
            ).bind(source_id=shooter.id, target_id=target.id)
        )


@register_ability
class DevoursCorpsesAbility(Ability):
    name = "DevoursCorpses"


@register_ability
class FerocityAbility(Ability):
    name = "Ferocity"
    main_schema = {
        "val": "Int",
    }


@register_ability
class RoundAttackAbility(Ability):
    name = "RoundAttack"


@register_ability
class ThreeSidedAttackAbility(Ability):
    name = "ThreeSidedAttack"


@register_ability
class ToxicCloudAttackAbility(Ability):
    name = "ToxicCloudAttack"


@register_ability
class FireballAttackAbility(Ability):
    name = "FireballAttack"


@register_ability
class WallDemolisherAbility(Ability):
    name = "WallDemolisher"
    main_schema = {
        "level": "Int",
    }
