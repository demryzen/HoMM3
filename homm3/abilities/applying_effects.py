from homm3.abilities import Ability, register_ability
from homm3.effects import EffectResult, effect_from_str
from homm3.enums import AttackType, EventType


@register_ability
class AttackEffectAbility(Ability):
    name = "AttackEffect"
    main_schema = {
        "attack": "AttackType",
        "moment": "AttackMoment",
        "target": "AttackTarget",
        "effect": "Effect",
        "probability": "Probability",
    }

    def _attack_matches(self, attack_type: AttackType) -> bool:
        return attack_type == self["attack"]

    def _event_type(self) -> EventType:
        if self["moment"] == "Before":
            return EventType.AttackStarted
        if self["moment"] == "After":
            return EventType.AttackEnded
        raise ValueError(f"Unknown attack effect moment: {self['moment']}")

    def _target_id(self, event) -> str:
        if self["target"] == "Attacker":
            return event.attacker_id
        if self["target"] == "Defender":
            return event.defender_id
        raise ValueError(f"Unknown attack effect target: {self['target']}")

    def on_event(self, event, controller) -> EffectResult:
        if event.type != self._event_type():
            return EffectResult.empty()

        if event.attacker_id != self.stack_id:
            return EffectResult.empty()

        if not self._attack_matches(event.attack_type):
            return EffectResult.empty()

        if controller.battle.rng.random() >= self["probability"]:
            return EffectResult.empty()

        target_id = self._target_id(event)
        target = controller.battle.id2stack(target_id)
        if target.is_died():
            return EffectResult.empty()

        effect = self["effect"].bind(
            source_id=event.attacker_id,
            target_id=target_id,
        )
        return EffectResult.effect(effect)


@register_ability
class TurnStartEffectAbility(Ability):
    name = "TurnStartEffect"
    main_schema = {
        "effect": "Effect",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turns = -1

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.TurnStarted:
            return EffectResult.empty()

        if event.stack_id != self.stack_id:
            return EffectResult.empty()

        if controller.battle.turn_queue.has_waited(self.stack_id):
            return EffectResult.empty()

        stack = controller.battle.id2stack(self.stack_id)
        if stack.extra_turn:
            return EffectResult.empty()

        self.turns += 1
        if self.turns % 3 != 0:
            return EffectResult.empty()

        target_id = None
        for stack in controller.battle.stacks():
            if stack.id != self.stack_id:
                target_id = stack.id
                break

        effect = self["effect"].bind(
            source_id=self.stack_id,
            target_id=target_id,
        )
        return EffectResult.effect(effect)


@register_ability
class InitialEffectAbility(Ability):
    name = "InitialEffect"
    main_schema = {
        "effect": "Effect",
    }

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.BattleStarted:
            return EffectResult.empty()

        effect = self["effect"].bind(
            source_id=None,
            target_id=self.stack_id,
        )
        effect.unblockable = True

        return EffectResult.effect(effect)
