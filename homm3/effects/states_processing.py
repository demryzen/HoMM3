from homm3.effects import Effect, EffectResult, register_effect
from homm3.enums import EffectType, Status
from homm3.states import state_from_str


class ApplyStateEffect(Effect):
    states: tuple[str, ...] = ()

    def create_states(self):
        result = []
        for state_name in self.states:
            state = state_from_str(state_name, params=self.state_params(state_name))
            state.source_id = self.source_id
            result.append(state)
        return result

    def state_params(self, state_name: str) -> dict:
        return self.params.copy()

    def apply(self, controller) -> EffectResult:
        result = EffectResult()

        for state in self.create_states():
            result.extend(controller.add_state(self.target_id, state))

        return result


@register_effect
class DispelEffect(Effect):
    name = "Dispel"
    main_schema = {
        "mode": "DispelArg",
    }
    effect_type = EffectType.Pure
    status = Status.Neutral
    log_applying = True

    def apply(self, controller) -> EffectResult:
        target = controller.battle.id2stack(self.target_id)
        result = EffectResult()

        for state in list(target.states):
            if not state.dispellable:
                continue
            if self["mode"] == "Positive" and state.status != Status.Positive:
                continue
            if self["mode"] == "Negative" and state.status != Status.Negative:
                continue
            result.extend(controller.remove_state(self.target_id, state.name))

        return result