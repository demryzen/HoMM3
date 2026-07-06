from copy import deepcopy
from typing import Any

from homm3.effects import EffectResult
from homm3.properties import Parametrized
from homm3.registry import Registry, parse_string


class Ability(Parametrized):
    name: str = "Ability"
    origin: tuple[str, ...] = ()

    def __init__(
        self,
        stack_id: str | None = None,
        params: dict[str, Any] | None = None,
    ):
        super().__init__(params=params)
        self.stack_id = stack_id

    @property
    def key(self) -> tuple:
        return self.name, self.stack_id

    def bind(self, stack_id: str) -> "Ability":
        ability = deepcopy(self)
        ability.stack_id = stack_id
        return ability

    def on_event(self, event, controller) -> EffectResult:
        return EffectResult.empty()


ABILITIES = Registry(base_cls=Ability, package_name="homm3.abilities", object_name="ability")


def ability_class(name: str) -> type[Ability] | None:
    return ABILITIES.get(name)


def ability_from_str(name: str, params: dict[str, Any] | None = None) -> Ability:
    return ABILITIES.create(name, params=params)


def abilities_from_str(s: str) -> list[Ability]:
    if not s:
        return []
    abilities = []
    for item in s.split(";"):
        stripped = item.strip()
        if len(stripped) == 0:
            continue
        name, args = parse_string(stripped)
        cls = ability_class(name)
        if cls is None:
            raise ValueError(f"Unknown ability: {name}!")
        if cls.origin:
            abilities.extend(abilities_from_str(";".join(cls.origin)))
            continue
        params = {param_name: value for param_name, value in zip(cls.main_schema, args)}
        abilities.append(ability_from_str(name, params=params))
    return abilities


def register_ability(cls=None, *, name: str | None = None, aliases: tuple[str, ...] = ()):
    return ABILITIES.register(cls, name=name, aliases=aliases)