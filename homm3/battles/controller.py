from homm3.effects import EffectResult, effect_from_str
from homm3.events.default_actions import StackMovedEvent, AttackStartedEvent, AttackEndedEvent, StackWaitedEvent, \
    StackDefendedEvent, StackReturnedEvent
from homm3.events.damage_outcomes import PhysicalDamageAppliedEvent, StackDiedEvent, ShotsChangedEvent, UnitsDiedEvent, InstantDamageAppliedEvent
from homm3.events.luck_morale import GoodMoraleTriggeredEvent, BadMoraleTriggeredEvent
from homm3.events.states_processing import StateAppliedEvent, StateRemovedEvent, StateAlreadyExistsEvent, StateProlongedEvent
from homm3.events.effects_processing import EffectBlockedEvent
from homm3.events.health_processing import StackHealedEvent
from homm3.states import State, state_from_str
from homm3.values import Value
from homm3.enums import AttackType, EffectType, Status, ActionType, EventType
from homm3.contexts import PhysicalDamageContext, StateApplicationContext
from homm3.units import Stack


class BattleController:
    def __init__(self, battle: "Battle"):
        self.battle = battle

    def perform_move(
        self,
        stack_id: str,
        speed: Value,
        steps: int,
    ) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        stack.run_up = abs(steps)
        if stack == self.battle.stack1:
            stack.position += steps
        else:
            stack.position -= steps
        return EffectResult.event(
            StackMovedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                speed_formula=speed.to_str(result=True),
                steps=steps,
            )
        )

    def perform_return(self, stack_id: str, steps: int) -> EffectResult:
        stack = self.battle.id2stack(stack_id)

        if stack.is_died():
            return EffectResult.empty()

        if stack == self.battle.stack1:
            stack.position -= steps
        else:
            stack.position += steps

        return EffectResult.event(
            StackReturnedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                steps=steps,
            )
        )

    def perform_wait(self, stack_id: str) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        self.battle.turn_queue.wait(stack_id)
        return EffectResult.event(
            StackWaitedEvent(stack_id=stack.id, stack=stack.name_count)
        )

    def perform_defense(self, stack_id: str) -> EffectResult:
        stack = self.battle.id2stack(stack_id)

        ctx = self.battle.context_factory.make_defense_action_context(stack_id)
        result = EffectResult.event(StackDefendedEvent(
            stack_id=stack.id,
            stack=stack.name_count,
            defense_formula=ctx.val.to_str(result=True)
        ))
        result.extend(
            self.add_state(
                stack_id,
                state_from_str("Defense", params={"val": ctx.val.total()}),
            )
        )

        return result

    def perform_strike(
            self,
            attacker_id: str,
            defender_id: str,
            is_retaliation: bool,
            is_preemptive: bool,
            is_additional: bool,
            additional_left: int = 0,
    ) -> EffectResult:
        attacker = self.battle.id2stack(attacker_id)
        defender = self.battle.id2stack(defender_id)
        result = EffectResult()

        if not self.can_perform_strike(attacker, defender):
            return result

        attack_result = self.perform_attack(
            attacker_id=attacker_id,
            defender_id=defender_id,
            attack_type=AttackType.Melee,
            attack_name="retaliates" if is_retaliation else "strikes",
            is_retaliation=is_retaliation,
            is_preemptive=is_preemptive,
            is_additional=is_additional,
        )
        result.extend(attack_result)

        n_died = 0
        for event in attack_result.events:
            if event.type == EventType.UnitsDied:
                n_died += event.n_died

        if is_retaliation:
            attacker.decrease_retaliations()

        return result

    def perform_shoot(
            self,
            shooter_id: str,
            target_id: str,
            is_retaliation: bool,
            is_preemptive: bool,
            is_additional: bool,
            additional_left: int = 0,
    ) -> EffectResult:
        result = EffectResult()

        shooter = self.battle.id2stack(shooter_id)
        target = self.battle.id2stack(target_id)
        if shooter.is_died() or target.is_died():
            return EffectResult.empty()
        if shooter.shots <= 0:
            return EffectResult.empty()

        shooter.shots -= 1
        shots_changed_event = ShotsChangedEvent(
            stack_id=shooter.id,
            stack=shooter.name_count,
            shots=shooter.shots,
            shots_base=shooter.shots_base,
        )

        result.extend(
            self.perform_attack(
                attacker_id=shooter_id,
                defender_id=target_id,
                attack_type=AttackType.Ranged,
                attack_name="shoots",
                is_retaliation=is_retaliation,
                is_preemptive=is_preemptive,
                is_additional=is_additional,
                before_damage_events=[shots_changed_event],
            )
        )

        if (not is_retaliation) and (not is_preemptive) and (not is_additional):
            additional_left = shooter.n_shoots - 1

        if (
                (additional_left > 0)
                and (not shooter.is_died())
                and (not target.is_died())
                and (shooter.shots > 0)
        ):
            result.effects.append(
                effect_from_str(
                    "Shoot",
                    params={
                        "is_retaliation": False,
                        "is_preemptive": False,
                        "is_additional": True,
                        "additional_left": additional_left - 1,
                    },
                ).bind(source_id=shooter.id, target_id=target.id)
            )

        return result

    def perform_attack(
            self,
            attacker_id: str,
            defender_id: str,
            attack_type: AttackType,
            attack_name: str,
            is_retaliation: bool,
            is_preemptive: bool,
            is_additional: bool,
            additional_left: int = 0,
            before_damage_events: list | None = None,
            after_damage_events: list | None = None,
    ) -> EffectResult:
        attacker = self.battle.id2stack(attacker_id)
        defender = self.battle.id2stack(defender_id)
        result = EffectResult()

        result.events.append(
            AttackStartedEvent(
                attacker_id=attacker.id,
                defender_id=defender.id,
                attacker=attacker.name_count,
                defender=defender.name_count,
                attack_name=attack_name,
                attack_type=attack_type,
                is_retaliation=is_retaliation,
                is_preemptive=is_preemptive,
                is_additional=is_additional,
            )
        )

        if before_damage_events:
            result.events.extend(before_damage_events)

        ctx = self.calculate_physical_damage(
            attacker_id=attacker_id,
            defender_id=defender_id,
            attack_type=attack_type,
            is_retaliation=is_retaliation,
        )
        damage_result = self.apply_physical_damage(
            attacker_id=attacker_id,
            defender_id=defender_id,
            damage=ctx.damage.total(),
            attack_formula=ctx.attack.to_str(result=True),
            defense_formula=ctx.defense.to_str(result=True),
            luck_formula=ctx.luck.to_str(result=True),
            damage_formula=ctx.damage.to_str(result=True),
            attack_type=attack_type,
            is_retaliation=is_retaliation,
        )
        result.extend(damage_result)

        n_died = 0
        for event in damage_result.events:
            if event.type == EventType.UnitsDied:
                n_died += event.n_died

        if after_damage_events:
            result.events.extend(after_damage_events)

        result.events.append(
            AttackEndedEvent(
                attacker_id=attacker.id,
                defender_id=defender.id,
                attacker=attacker.name_count,
                defender=defender.name_count,
                attack_type=attack_type,
                is_retaliation=is_retaliation,
                is_preemptive=is_preemptive,
                is_additional=is_additional,
                n_died=n_died,
                additional_left=additional_left,
            )
        )

        return result

    def process_attack_followups(self, event) -> EffectResult:
        if event.type != EventType.AttackEnded:
            return EffectResult.empty()

        if event.attack_type != AttackType.Melee:
            return EffectResult.empty()

        attacker = self.battle.id2stack(event.attacker_id)
        defender = self.battle.id2stack(event.defender_id)

        result = EffectResult()

        if self.can_retaliate(
                attacker,
                defender,
                event.is_retaliation,
                event.is_preemptive,
                event.is_additional,
        ):
            result.effects.append(
                effect_from_str(
                    "Strike",
                    params={
                        "is_retaliation": True,
                        "is_preemptive": False,
                        "is_additional": False,
                    },
                ).bind(source_id=defender.id, target_id=attacker.id)
            )

        additional_left = event.additional_left
        if (not event.is_retaliation) and (not event.is_preemptive) and (not event.is_additional):
            additional_left = attacker.n_strikes - 1
            if (event.n_died > 0) and attacker.has_ability("Ferocity"):
                additional_left += attacker.get_ability("Ferocity")["val"]

        if (additional_left > 0) and self.can_perform_strike(attacker, defender):
            result.effects.append(
                effect_from_str(
                    "Strike",
                    params={
                        "is_retaliation": False,
                        "is_preemptive": False,
                        "is_additional": True,
                        "additional_left": additional_left - 1,
                    },
                ).bind(source_id=attacker.id, target_id=defender.id)
            )

        return result

    def calculate_physical_damage(
        self,
        attacker_id: str,
        defender_id: str,
        attack_type: AttackType,
        is_retaliation: bool = False,
    ) -> PhysicalDamageContext:
        return self.battle.context_factory.make_physical_damage_context(
            attacker_id=attacker_id,
            defender_id=defender_id,
            attack_type=attack_type,
            is_retaliation=is_retaliation,
        )

    def apply_physical_damage(
            self,
            attacker_id: str,
            defender_id: str,
            damage: int,
            attack_formula: str | None = None,
            defense_formula: str | None = None,
            luck_formula: str | None = None,
            damage_formula: str | None = None,
            attack_type: AttackType | None = None,
            is_retaliation: bool = False,
    ) -> EffectResult:
        attacker = self.battle.id2stack(attacker_id)
        defender = self.battle.id2stack(defender_id)

        damage_received = min(damage, defender.health_all)
        n_died = defender.apply_damage(damage)

        result = EffectResult.event(
            PhysicalDamageAppliedEvent(
                attacker_id=attacker.id,
                defender_id=defender.id,
                attacker=attacker.name_count,
                defender=defender.name_count,
                damage=damage,
                damage_received=damage_received,
                attack_formula="" if attack_formula is None else attack_formula,
                defense_formula="" if defense_formula is None else defense_formula,
                luck_formula="" if luck_formula is None else luck_formula,
                damage_formula=str(damage) if damage_formula is None else damage_formula,
                attack_type=attack_type,
                is_retaliation=is_retaliation,
            )
        )

        if n_died > 0:
            result.events.append(
                UnitsDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    n_died=n_died,
                )
            )

        if defender.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    killed_by_id=attacker.id,
                    n_died=n_died
                )
            )
            self.battle.finished = True
            self.battle.winner = attacker

        return result

    def apply_instant_damage(
            self,
            attacker_id: str,
            defender_id: str,
            damage: int,
            damage_formula: str | None = None,
    ) -> EffectResult:
        attacker = self.battle.id2stack(attacker_id)
        defender = self.battle.id2stack(defender_id)

        damage_received = min(damage, defender.health_all)
        n_died = defender.apply_damage(damage)

        result = EffectResult.event(
            InstantDamageAppliedEvent(
                attacker_id=attacker_id,
                defender_id=defender_id,
                damage=damage,
                damage_received=damage_received,
                damage_formula=str(damage) if damage_formula is None else damage_formula,
            )
        )

        if n_died > 0:
            result.events.append(
                UnitsDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    n_died=n_died,
                )
            )

        if defender.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    killed_by_id=attacker.id,
                    n_died=n_died
                )
            )
            self.battle.finished = True
            self.battle.winner = attacker

        return result

    def apply_magical_damage(
            self,
            attacker_id: str | None,
            defender_id: str,
            effect,
            damage: int,
    ) -> EffectResult:
        defender = self.battle.id2stack(defender_id)
        ctx = self.battle.context_factory.make_magical_damage_context(
            attacker_id=attacker_id,
            defender_id=defender_id,
            effect=effect,
            damage=damage,
        )

        damage_total = ctx.damage.total()
        damage_received = min(damage_total, defender.health_all)
        n_died = defender.apply_damage(damage_total)

        result = EffectResult.event(
            InstantDamageAppliedEvent(
                attacker_id="" if attacker_id is None else attacker_id,
                defender_id=defender_id,
                damage=damage_total,
                damage_received=damage_received,
                damage_formula=ctx.damage.to_str(result=True),
            )
        )

        if n_died > 0:
            result.events.append(
                UnitsDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    n_died=n_died,
                )
            )

        if defender.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=defender.id,
                    stack=defender.name_count,
                    killed_by_id="" if attacker_id is None else attacker_id,
                    n_died=n_died
                )
            )
            self.battle.finished = True
            self.battle.winner = None if attacker_id is None else self.battle.id2stack(attacker_id)

        return result

    def apply_good_morale(self, stack_id: str) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        stack.extra_turn = True
        stack.actions_left += 1
        return EffectResult.event(GoodMoraleTriggeredEvent(stack_id=stack.id, stack=stack.name_count))

    def apply_bad_morale(self, stack_id: str) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        stack.actions_left = 0
        return EffectResult.event(BadMoraleTriggeredEvent(stack_id=stack.id, stack=stack.name_count))

    def apply_heal(self, stack_id: str, hp: int | None = None) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        if stack.is_died():
            return EffectResult.empty()
        hp_restored = stack.heal(hp)
        return EffectResult.event(
            StackHealedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                hp=hp,
                hp_restored=hp_restored,
            )
        )

    def get_state(self, stack_id: str, state_name: str) -> State | None:
        stack = self.battle.id2stack(stack_id)
        for state in stack.states:
            if state.name == state_name:
                return state
        return None

    def add_state(self, stack_id: str, state: State) -> EffectResult:
        stack = self.battle.id2stack(stack_id)
        state = state.bind(stack_id=stack_id, source_id=state.source_id)

        ctx = StateApplicationContext(stack_id=stack_id, state=state)
        self.battle.context_factory.apply_modifiers("modify_state_application", ctx)
        state = ctx.state

        result = EffectResult()

        for cancelled_name in state.cancel:
            existing = self.get_state(stack_id, cancelled_name)
            if existing is None:
                continue
            existing.expire()

        existing = self.get_state(stack_id, state.name)
        if existing is not None:
            if not state.cumulative:
                result.events.append(
                    StateAlreadyExistsEvent(
                        stack_id=stack.id,
                        stack=stack.name_count,
                        state=str(state),
                    )
                )
                return result

            prolong_result = existing.on_prolong(state, self)
            result.events.append(
                StateProlongedEvent(
                    stack_id=stack.id,
                    stack=stack.name_count,
                    state=str(existing),
                )
            )
            result.extend(prolong_result)
            result.extend(self.cleanup_states())
            return result

        stack.states.append(state)

        result.extend(state.on_apply(self))
        result.events.append(
            StateAppliedEvent(
                stack_id=stack.id,
                stack=stack.name_count,
                state=str(state),
            )
        )
        result.extend(self.cleanup_states())
        return result

    def remove_state(self, stack_id: str, state_name: str) -> EffectResult:
        state = self.get_state(stack_id, state_name)
        if state is None:
            return EffectResult.empty()

        state.expire()
        return self.cleanup_states()

    def cleanup_states(self) -> EffectResult:
        result = EffectResult()
        view = self.battle.view()

        for stack in self.battle.stacks():
            active_states = []

            for state in stack.states:
                if state.is_active(view):
                    active_states.append(state)
                    continue

                result.extend(state.on_remove(self))
                result.events.append(
                    StateRemovedEvent(
                        stack_id=stack.id,
                        stack=stack.name_count,
                        state=str(state),
                    )
                )

            stack.states = active_states

        return result

    def process_state_event(self, event) -> EffectResult:
        result = EffectResult()

        for stack in self.battle.stacks():
            for state in list(stack.states):
                result.extend(state.on_event(event, self))

        result.extend(self.cleanup_states())
        return result

    def process_ability_event(self, event) -> EffectResult:
        result = EffectResult()

        for stack in self.battle.stacks():
            for ability in list(stack.abilities):
                result.extend(ability.on_event(event, self))

        return result

    def can_retaliate(
            self,
            attacker: Stack,
            defender: Stack,
            is_retaliation: bool,
            is_preemptive: bool,
            is_additional: bool,
    ) -> bool:
        if is_retaliation or is_preemptive or is_additional:
            return False
        if attacker.is_died() or defender.is_died():
            return False
        if attacker.has_ability("IgnoreRetaliation"):
            return False
        if defender.has_state("Hypnotized"):
            return False
        if defender.has_state("Stoned"):
            return False
        if defender.has_state("Paralysed"):
            return False
        if defender.has_state("Blinded"):
            return False
        if defender.has_state("SkipRetaliation"):
            return False
        if isinstance(defender.retaliations, int) and (defender.retaliations == 0):
            return False
        if self.battle.distance > 0:
            return False
        return True

    def can_perform_strike(self, attacker: Stack, defender: Stack) -> bool:
        if attacker.is_died() or defender.is_died():
            return False
        ctx = self.battle.context_factory.make_action_context(attacker.id)
        action = ctx.get(ActionType.Strike)
        return (action is not None) and (action.target_id == defender.id)

    def effect_allowed_by_filters(self, effect, target) -> bool:
        if not effect.allow_filters:
            return True
        return all(filter_.matches(target) for filter_ in effect.allow_filters)

    def effect_blocked_by_filters(self, effect, target) -> bool:
        return any(filter_.matches(target) for filter_ in effect.block_filters)

    def check_effect_blocked(self, effect) -> EffectBlockedEvent | None:
        if effect.unblockable:
            return None

        if effect.target_id is None:
            return None

        target = self.battle.id2stack(effect.target_id)

        if not self.effect_allowed_by_filters(effect, target):
            return EffectBlockedEvent(
                stack_id=target.id,
                stack=target.name_count,
                effect=str(effect),
                reason="Filter",
            )

        if self.effect_blocked_by_filters(effect, target):
            return EffectBlockedEvent(
                stack_id=target.id,
                stack=target.name_count,
                effect=str(effect),
                reason="Filter",
            )

        if (not effect.ignore_immunity) and target.is_immune_to_effect(effect):
            return EffectBlockedEvent(
                stack_id=target.id,
                stack=target.name_count,
                effect=str(effect),
                reason="Immunity",
            )

        if (not effect.ignore_spell_resistance) and (effect.effect_type == EffectType.Magical) and (effect.status == Status.Negative):
            prob = target.spell_resistance_probability()
            if self.battle.rng.random() < prob:
                return EffectBlockedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    effect=str(effect),
                    reason="SpellResistance",
                )

        return None
