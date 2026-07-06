from homm3.abilities import Ability, register_ability
from homm3.contexts import PhysicalDamageContext, SpeedContext
from homm3.effects import EffectResult
from homm3.enums import ActionType, EventType
from homm3.events.damage_outcomes import StackDetonatedEvent, UnitsDiedEvent, StackDiedEvent
from homm3.events.special_events import RuneLevelIncreasedEvent
from homm3.values import Term


@register_ability
class PossessRunesAbility(Ability):
    name = "PossessRunes"
    main_schema = {
        "max_level": "Int",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.level = 0
        self.health_before_action = None
        self.action_type = None

    def add_runes(self, delta: int, controller) -> EffectResult:
        if self.level >= self["max_level"]:
            return EffectResult.empty()

        stack = controller.battle.id2stack(self.stack_id)
        if stack.is_died():
            return EffectResult.empty()

        before = self.level
        self.level = min(self.level + delta, self["max_level"])
        actual_delta = self.level - before

        if actual_delta <= 0:
            return EffectResult.empty()

        return EffectResult.event(
            RuneLevelIncreasedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                delta=actual_delta,
                level=self.level,
            )
        )

    def on_event(self, event, controller) -> EffectResult:
        if (event.type == EventType.ActionSelected) and (event.stack_id == self.stack_id):
            stack = controller.battle.id2stack(self.stack_id)
            self.health_before_action = stack.health_all
            self.action_type = event.action
            return EffectResult.empty()

        if (event.type == EventType.ActionEnded) and (event.stack_id == self.stack_id):
            if self.action_type not in {ActionType.Strike, ActionType.MoveAndStrike, ActionType.Shoot}:
                return EffectResult.empty()
            stack = controller.battle.id2stack(self.stack_id)
            if self.health_before_action == stack.health_all:
                return self.add_runes(1, controller)
            return EffectResult.empty()

        if (event.type == EventType.DamageApplied) and (event.defender_id == self.stack_id):
            if event.damage_received > 0:
                return self.add_runes(2, controller)
            return EffectResult.empty()

        if (event.type == EventType.StackDefended) and (event.stack_id == self.stack_id):
            return self.add_runes(3, controller)

        return EffectResult.empty()

    def modify_physical_damage(self, ctx: PhysicalDamageContext, view):
        if ctx.attacker_id == self.stack_id:
            bonus = ((self.level + 2) // 3) * 2
            if bonus > 0:
                ctx.attack["base"].add(Term(bonus, label=f"Runes(level={self.level})"))

        if ctx.defender_id == self.stack_id:
            bonus = ((self.level + 1) // 3) * 2
            if bonus > 0:
                ctx.defense["base"].add(Term(bonus, label=f"Runes(level={self.level})"))

    def modify_speed(self, ctx: SpeedContext, view):
        if ctx.stack_id != self.stack_id:
            return

        bonus = self.level // 3
        if bonus > 0:
            ctx.speed["base"].add(Term(bonus, label=f"Runes(level={self.level})"))


@register_ability
class AcidBreathAbility(Ability):
    name = "AcidBreath"
    origin = (
        "AttackEffect(Melee,After,Defender,AcidCorrosion(3),100)",
        "AttackEffect(Melee,After,Defender,InstantPhysicalDamagePerUnit(25),20)",
    )


@register_ability
class DetonationAbility(Ability):
    name = "Detonation"

    def on_event(self, event, controller) -> EffectResult:
        if event.type != EventType.StackDied:
            return EffectResult.empty()

        if event.stack_id != self.stack_id:
            return EffectResult.empty()

        if controller.battle.distance > 0:
            return EffectResult.empty()

        source = controller.battle.id2stack(self.stack_id)
        target = next(stack for stack in controller.battle.stacks() if stack.id != self.stack_id)

        if target.is_died():
            return EffectResult.empty()

        damage = 90 + 5 * event.n_died
        damage_received = min(damage, target.health_all)
        n_died = target.apply_damage(damage)

        result = EffectResult.event(
            StackDetonatedEvent(
                source_id=source.id,
                target_id=target.id,
                source=source.name_count,
                target=target.name_count,
                damage=damage,
                damage_received=damage_received,
            )
        )

        if n_died > 0:
            result.events.append(
                UnitsDiedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    n_died=n_died,
                )
            )

        if target.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    killed_by_id=source.id,
                    n_died=n_died,
                )
            )

            controller.battle.finished = True
            controller.battle.winner = None

        return result
