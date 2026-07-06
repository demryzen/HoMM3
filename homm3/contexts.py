from dataclasses import dataclass, field
from typing import Any

import numpy as np

from homm3.values import Value, GroupedRandomValue, Product, Sum, Term
from homm3.enums import AttackType, ActionType
from homm3.params import GOOD_LUCK_PROBS, BAD_LUCK_PROBS, RANGE_PENALTY_DISTANCE


@dataclass(slots=True)
class AvailableAction:
    type: ActionType
    source_id: str
    target_id: str | None = None
    effect: str = ""
    ability: Any = None
    is_free: bool = False
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple:
        return self.type, self.source_id, self.target_id, self.effect

    def modify(self, **params) -> "AvailableAction":
        merged = self.params.copy()
        merged.update(params)
        return AvailableAction(
            type=self.type,
            source_id=self.source_id,
            target_id=self.target_id,
            effect=self.effect,
            is_free=self.is_free,
            params=merged,
        )


@dataclass(slots=True)
class ActionContext:
    stack_id: str
    enemy_id: str
    distance: int
    stack_speed: int
    enemy_speed: int
    is_faster: bool
    is_waited: bool
    actions: list[AvailableAction] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    rng: np.random.Generator | None = None

    def add(self, action: AvailableAction):
        self.actions.append(action)

    def remove(self, action_type: ActionType, reason: str | None = None):
        before = len(self.actions)
        self.actions = [a for a in self.actions if a.type != action_type]
        if (len(self.actions) != before) and (reason is not None):
            self.reasons.append(reason)

    def clear(self, reason: str):
        self.actions.clear()
        self.reasons.append(reason)

    def get(self, action_type: ActionType) -> AvailableAction | None:
        for action in self.actions:
            if action.type == action_type:
                return action
        return None

    def has(self, action_type: ActionType) -> bool:
        return self.get(action_type) is not None

    def remove_target(self, target_id: str, reason: str | None = None):
        before = len(self.actions)
        self.actions = [action for action in self.actions if action.target_id != target_id]
        if (len(self.actions) != before) and (reason is not None):
            self.reasons.append(reason)

    def copy_with_actions(self, actions: list[AvailableAction]) -> "ActionContext":
        return ActionContext(
            stack_id=self.stack_id,
            enemy_id=self.enemy_id,
            distance=self.distance,
            stack_speed=self.stack_speed,
            enemy_speed=self.enemy_speed,
            is_faster=self.is_faster,
            is_waited=self.is_waited,
            actions=actions,
            reasons=self.reasons.copy(),
            rng=self.rng,
        )


@dataclass(slots=True)
class DefenseActionContext:
    stack_id: str
    val: Value


@dataclass(slots=True)
class SpeedContext:
    stack_id: str
    speed: Value


@dataclass(slots=True)
class BaseDamageContext:
    attacker_id: str
    value_min: int
    value_max: int
    count: int
    rng: np.random.Generator | None = None
    reasons: list[str] = field(default_factory=list)

    def set_fixed(self, value: int, reason: str):
        value = max(0, value)
        self.value_min = value
        self.value_max = value
        self.reasons.append(reason)

    def use_max(self, bonus: int = 0, reason: str = "Max damage"):
        self.set_fixed(self.value_max + bonus, reason)

    def use_min(self, penalty: int = 0, reason: str = "Min damage"):
        self.set_fixed(self.value_min - penalty, reason)

    def build(self) -> GroupedRandomValue:
        label = "Base damage"
        if self.reasons:
            label += f" ({', '.join(self.reasons)})"

        return GroupedRandomValue(
            self.value_min,
            self.value_max,
            self.count,
            rng=self.rng,
            label=label,
            )


@dataclass(slots=True)
class PhysicalDamageContext:
    attacker_id: str
    defender_id: str
    attack_type: AttackType
    is_retaliation: bool
    attack: Value
    defense: Value
    luck: Value
    luck_coeff: float
    damage: Value
    reasons: list[str] = field(default_factory=list)
    rng: np.random.Generator | None = None


@dataclass(slots=True)
class MagicalDamageContext:
    attacker_id: str | None
    defender_id: str
    effect: "Effect"
    damage: Value


@dataclass(slots=True)
class MoraleContext:
    stack_id: str
    enemy_id: str
    morale: Value


@dataclass(slots=True)
class StateApplicationContext:
    stack_id: str
    state: "State"


class ContextFactory:
    def __init__(self, battle):
        self.battle = battle

    def make_speed_context(self, stack_id: str) -> SpeedContext:
        stack = self.battle.id2stack(stack_id)

        ctx = SpeedContext(
            stack_id=stack.id,
            speed=Value(stack.speed_base, name="base", round_method="round", min_value=0),
        )

        self.apply_modifiers("modify_speed", ctx)
        return ctx

    def make_base_damage_context(self, attacker_id: str) -> BaseDamageContext:
        attacker = self.battle.id2stack(attacker_id)
        dmg_min, dmg_max = attacker.damage_base

        ctx = BaseDamageContext(
            attacker_id=attacker_id,
            value_min=dmg_min,
            value_max=dmg_max,
            count=attacker.count,
            rng=self.battle.rng,
            reasons=[],
        )

        self.apply_modifiers("modify_base_damage", ctx)
        return ctx

    def make_physical_damage_context(
        self,
        attacker_id: str,
        defender_id: str,
        attack_type: AttackType,
        is_retaliation: bool = False,
    ) -> PhysicalDamageContext:
        attacker = self.battle.id2stack(attacker_id)
        defender = self.battle.id2stack(defender_id)

        base_ctx = self.make_base_damage_context(attacker_id)

        attack = Value(attacker.attack_base, name="base", round_method="round", min_value=0).mul(Product(name="factors"))
        defense = Value(defender.defense_base, name="base", round_method="round", min_value=0).mul(Product(name="factors"))
        luck = Value(attacker.luck_base, name="base", round_method="round")

        base_damage = base_ctx.build()
        damage = Value(base_damage, name="base", round_method="round")
        damage = damage.mul(Sum(terms=[1], name="factor_sum")).mul(Product(name="factor_prod"))

        ctx = PhysicalDamageContext(
            attacker_id=attacker_id,
            defender_id=defender_id,
            attack_type=attack_type,
            is_retaliation=is_retaliation,
            attack=attack,
            defense=defense,
            luck=luck,
            luck_coeff=1.0,
            damage=damage,
            reasons=[],
            rng=self.battle.rng,
        )

        self.apply_modifiers("modify_physical_damage", ctx)

        if (attack_type == AttackType.Melee) and attacker.is_ranged() and (not attacker.has_ability("NoMeleePenalty")):
            ctx.damage["factor_prod"].mul(Term(0.5, label="Melee penalty"))

        if (attack_type == AttackType.Ranged) and (self.battle.distance >= RANGE_PENALTY_DISTANCE) and (not attacker.has_ability("NoRangePenalty")):
            ctx.damage["factor_prod"].mul(Term(0.5, label="Range penalty"))

        attack_total = ctx.attack.total()
        defense_total = ctx.defense.total()
        attack_modifier = self._damage_attack_modifier(attack_total, defense_total)
        ctx.damage["factor_sum"].add(Term(attack_modifier, label="Attack modifier"))
        defense_modifier = self._damage_defense_modifier(attack_total, defense_total)
        ctx.damage["factor_prod"].mul(Term(defense_modifier, label="Defense modifier"))

        luck_modifier = self._damage_luck_modifier(ctx.luck, ctx.luck_coeff, rng=ctx.rng)
        if (luck_modifier is not None) and self.battle.use_luck:
            damage["factor_prod"].mul(luck_modifier)

        return ctx

    def make_magical_damage_context(
            self,
            attacker_id: str | None,
            defender_id: str,
            effect: "Effect",
            damage: int,
    ) -> MagicalDamageContext:
        ctx = MagicalDamageContext(
            attacker_id=attacker_id,
            defender_id=defender_id,
            effect=effect,
            damage=Value(damage, name="base", round_method="round", min_value=0).mul(Product(name="factor_prod")),
        )
        self.apply_modifiers("modify_magical_damage", ctx)
        return ctx

    def make_action_context(self, stack_id: str) -> ActionContext:
        stack = self.battle.id2stack(stack_id)
        enemy = self.battle.stack1 if stack_id != self.battle.stack1.id else self.battle.stack2

        stack_speed_val = self.make_speed_context(stack_id).speed
        enemy_speed_val = self.make_speed_context(enemy.id).speed

        stack_speed = stack_speed_val.total()
        enemy_speed = enemy_speed_val.total()
        distance = self.battle.distance
        is_faster = (stack_speed > enemy_speed) or (stack_speed == enemy_speed and stack == self.battle.stack1)

        ctx = ActionContext(
            stack_id=stack_id,
            enemy_id=enemy.id,
            distance=distance,
            stack_speed=stack_speed,
            enemy_speed=enemy_speed,
            is_faster=is_faster,
            is_waited=self.battle.turn_queue.has_waited(stack_id),
            rng=self.battle.rng,
        )

        ctx.add(
            AvailableAction(
                type=ActionType.Defense,
                source_id=stack_id,
                effect="Defense",
            )
        )

        if not ctx.is_waited:
            ctx.add(
                AvailableAction(
                    type=ActionType.Wait,
                    source_id=stack_id,
                    effect="Wait",
                )
            )

        if (distance > 0) and (stack_speed > 0):
            steps = min(stack_speed, distance)
            ctx.add(
                AvailableAction(
                    type=ActionType.Move,
                    source_id=stack_id,
                    effect="Move",
                    params={
                        "steps": steps,
                        "speed": stack_speed_val,
                    },
                )
            )

        if distance == 0:
            ctx.add(
                AvailableAction(
                    type=ActionType.Strike,
                    source_id=stack_id,
                    target_id=enemy.id,
                    effect="Strike",
                )
            )
        elif stack_speed >= distance:
            ctx.add(
                AvailableAction(
                    type=ActionType.MoveAndStrike,
                    source_id=stack_id,
                    target_id=enemy.id,
                    effect="MoveAndStrike",
                    params={
                        "steps": distance,
                        "speed": stack_speed_val,
                    },
                )
            )

        if (stack.shots > 0) and (distance > 0):
            ctx.add(
                AvailableAction(
                    type=ActionType.Shoot,
                    source_id=stack_id,
                    target_id=enemy.id,
                    effect="Shoot",
                )
            )

        self.apply_modifiers("modify_actions", ctx)
        return ctx

    def make_defense_action_context(self, stack_id: str) -> DefenseActionContext:
        ctx = DefenseActionContext(
            stack_id=stack_id,
            val=Value(20, name="base", round_method="round", min_value=0),
        )
        self.apply_modifiers("modify_defense_action", ctx)
        return ctx

    def make_morale_context(self, stack_id: str) -> MoraleContext:
        stack = self.battle.id2stack(stack_id)
        enemy = self.battle.stack1 if stack_id != self.battle.stack1.id else self.battle.stack2

        ctx = MoraleContext(
            stack_id=stack_id,
            enemy_id=enemy.id,
            morale=Value(stack.morale_base, name="base", round_method="round", min_value=-3, max_value=3)
        )

        self.apply_modifiers("modify_morale", ctx)
        return ctx

    def apply_modifiers(self, hook_name: str, ctx):
        modifiers = sorted(
            self.battle.get_all_modifiers(),
            key=lambda modifier: 0 if modifier.priority is None else modifier.priority,
        )
        for modifier in modifiers:
            hook = getattr(modifier, hook_name, None)
            if hook is not None:
                hook(ctx, self.battle.view())

    @staticmethod
    def _damage_attack_modifier(attack: float | int, defense: float | int) -> float:
        return max(0.0, min(3.0, 0.05 * (attack - defense)))

    @staticmethod
    def _damage_defense_modifier(attack: float | int, defense: float | int) -> float:
        return max(0.3, min(1.0, 1.0 - 0.025 * (defense - attack)))

    @staticmethod
    def _damage_luck_modifier(luck: Value, coeff: float = 1.0, rng: np.random.Generator | None = None) -> Term | None:
        if not (luck_val := luck.total()):
            return None
        luck_val = max(-3, min(3, luck_val))
        is_good = luck_val > 0
        probs = GOOD_LUCK_PROBS if is_good else BAD_LUCK_PROBS
        prob = probs[abs(luck_val) - 1]
        rng = rng or np.random.default_rng()
        if rng.random() < (coeff * prob):
            modifier = 2.0 if is_good else 0.5
            msg = "Fortune!" if is_good else "Misfortune"
            return Term(modifier, f"Luck modifier: {msg}")
        return None
