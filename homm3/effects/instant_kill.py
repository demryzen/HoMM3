import numpy as np

from homm3.effects import register_effect, Effect, EffectResult
from homm3.enums import Status, EffectType, UnitEntity
from homm3.filters import EntityFilter
from homm3.params import RANGE_PENALTY_DISTANCE
from homm3.events.damage_outcomes import UnitsInstantKilledEvent, StackDiedEvent


@register_effect
class AccurateShotEffect(Effect):
    name = "AccurateShot"
    main_schema = {
        "p_range_penalty": "Probability",
        "p_no_penalty": "Probability",
    }
    status = Status.Negative
    effect_type = EffectType.Pure
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )

    def apply(self, controller) -> EffectResult:
        target = controller.battle.id2stack(self.target_id)

        probability = (
            self["p_range_penalty"]
            if controller.battle.distance >= RANGE_PENALTY_DISTANCE
            else self["p_no_penalty"]
        )

        kills = controller.battle.rng.binomial(n=target.count, p=probability)
        max_kills = int(np.ceil(target.count * probability))
        n_killed = target.kill_units(min(kills, max_kills))

        if n_killed > 0:
            result = EffectResult.event(
                UnitsInstantKilledEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    reason="Accurate shot",
                    n_killed=n_killed,
                )
            )
        else:
            result = EffectResult.empty()

        if target.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    killed_by_id=self.source_id,
                    n_died=n_killed,
                )
            )
            controller.battle.finished = True
            controller.battle.winner = controller.battle.id2stack(self.source_id)

        return result


@register_effect
class DeathStareEffect(Effect):
    name = "DeathStare"
    main_schema = {
        "probability": "Probability",
    }
    status = Status.Negative
    effect_type = EffectType.Pure
    allow_filters = (
        EntityFilter((UnitEntity.Living,)),
    )

    def apply(self, controller) -> EffectResult:
        source = controller.battle.id2stack(self.source_id)
        target = controller.battle.id2stack(self.target_id)

        probability = self["probability"]
        probability_percent = probability * 100

        kills = controller.battle.rng.binomial(
            n=source.count,
            p=probability,
        )
        max_kills = int(np.ceil(source.count / probability_percent))
        n_killed = target.kill_units(min(kills, max_kills))

        if n_killed > 0:
            result = EffectResult.event(
                UnitsInstantKilledEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    reason="Death stare",
                    n_killed=n_killed,
                )
            )
        else:
            result = EffectResult.empty()

        if target.is_died():
            result.events.append(
                StackDiedEvent(
                    stack_id=target.id,
                    stack=target.name_count,
                    killed_by_id=self.source_id,
                    n_died=n_killed,
                )
            )
            controller.battle.finished = True
            controller.battle.winner = source

        return result
