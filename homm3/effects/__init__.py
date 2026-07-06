from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy

from homm3.enums import Status, EffectType, EffectElement, EffectDomain
from homm3.properties import Parametrized
from homm3.registry import Registry, parse_string


@dataclass
class EffectResult:
    events: list["Event"] = field(default_factory=list)
    effects: list["Effect"] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "EffectResult":
        return cls()

    @classmethod
    def event(cls, event: "Event") -> "EffectResult":
        return cls(events=[event])

    @classmethod
    def effect(cls, effect: "Effect") -> "EffectResult":
        return cls(effects=[effect])

    def extend(self, other: "EffectResult"):
        self.events.extend(other.events)
        self.effects.extend(other.effects)


class Effect(Parametrized):
    name: str = "Effect"
    effect_type: EffectType | None = None
    status: Status | None = None
    element: EffectElement | None = None
    domains: tuple[EffectDomain, ...] = ()
    level: int | None = None
    allow_filters: tuple = ()
    block_filters: tuple = ()
    unblockable: bool = False
    ignore_immunity: bool = False
    ignore_spell_resistance: bool = False
    log_applying: bool = False
    log_label: str | None = None

    def __init__(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        params: dict[str, Any] | None = None,
    ):
        super().__init__(params=params)
        self.source_id = source_id
        self.target_id = target_id

    def bind(self, source_id: str | None = None, target_id: str | None = None) -> "Effect":
        effect = deepcopy(self)
        effect.source_id = source_id
        effect.target_id = target_id
        return effect

    def apply(self, controller: "BattleController") -> EffectResult:
        return EffectResult.empty()


EFFECTS = Registry(base_cls=Effect, package_name="homm3.effects", object_name="effect")


def effect_class(name: str) -> type[Effect] | None:
    return EFFECTS.get(name)


def effect_from_str(name: str, params: dict[str, Any] | None = None) -> Effect:
    if params is not None:
        return EFFECTS.create(name, params=params)

    effect_name, args = parse_string(name)
    cls = effect_class(effect_name)
    if cls is None:
        raise ValueError(f"Unknown effect: {effect_name}!")

    parsed_params = {
        param_name: value
        for param_name, value in zip(cls.main_schema, args)
    }

    return EFFECTS.create(effect_name, params=parsed_params)


def register_effect(cls=None, *, name: str | None = None, aliases: tuple[str, ...] = ()):
    return EFFECTS.register(cls, name=name, aliases=aliases)