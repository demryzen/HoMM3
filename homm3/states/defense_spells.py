from homm3.effects import EffectResult, effect_from_str
from homm3.enums import EventType, AttackType, SpellMastery
from homm3.states import State, register_state


@register_state
class FireShieldState(State):
    name = "FireShield"
    main_schema = {
        "mastery": "Mastery",
        "rounds": "Int|Str",
    }
    cumulative = True

    def on_event(self, event, controller) -> EffectResult:
        result = super().on_event(event, controller)

        if event.type != EventType.DamageApplied:
            return result

        if not hasattr(event, "attack_type"):
            return result

        if event.defender_id != self.stack_id:
            return result

        if event.attack_type != AttackType.Melee:
            return result

        val = {
            SpellMastery.No: 20,
            SpellMastery.Basic: 20,
            SpellMastery.Advanced: 25,
            SpellMastery.Expert: 30,
        }[self["mastery"]]

        damage = int(event.damage_received * val / 100)
        if damage <= 0:
            return result

        result.effects.append(
            effect_from_str(
                "FireShieldDamage",
                params={"damage": damage},
            ).bind(
                source_id=self.stack_id,
                target_id=event.attacker_id,
            )
        )

        return result
