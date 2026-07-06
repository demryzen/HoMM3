from dataclasses import dataclass
from collections import Counter

import numpy as np

from homm3.resources import ResourcePool
from homm3.enums import UnitHome, UnitMovement, UnitEntity, EffectDomain, Resource
from homm3.db import DataBase
from homm3.abilities import Ability, abilities_from_str
from homm3.effects import Effect
from homm3.filters import Filter


REGISTER = Counter()


@dataclass(slots=True)
class Unit:
    name: str
    attack: int
    defense: int
    damage: tuple[int, int]
    health: int
    speed: int
    growth: int
    size: int
    shots: int
    tier: int
    grade: int
    cost: ResourcePool
    movement: UnitMovement
    home: UnitHome
    source_name: str
    source_version: str
    entity: UnitEntity
    upgrade: str
    abilities: list[Ability]

    @staticmethod
    def from_db(name: str) -> "Unit":
        result = DataBase.request(f"""SELECT * FROM Units WHERE Units.name = '{name}'""")
        if result.empty:
            raise Exception(f"No unit '{name}' in database!")
        params_series = result.loc[0]

        params_dict = {"name": name}
        for field in ("attack", "defense", "health", "speed", "growth", "size", "shots", "tier", "grade", "source_name", "source_version"):
            params_dict[field] = params_series[field]

        params_dict["damage"] = (params_series["damage_min"], params_series["damage_max"])
        params_dict["home"] = UnitHome.from_str(params_series["home"].capitalize())
        params_dict["movement"] = UnitMovement.from_str(params_series["movement"].capitalize())
        params_dict["entity"] = UnitEntity.from_str(params_series["entity"].capitalize())
        params_dict["cost"] = ResourcePool.from_str(params_series["cost"])
        params_dict["upgrade"] = params_series["upgrade"]
        params_dict["abilities"] = abilities_from_str(params_series["abilities"])

        return Unit(**params_dict)

    @property
    def id(self) -> str:
        return self.name.lower().replace(" ", "_")

    def info(self, full: bool = False) -> str:
        if full:
            info = f"{self.name} ({self.home}) [Tier {self.tier}.{self.grade}]\n"
        else:
            info = f"{self.name}\n"
        info += f"Attack: {self.attack}\n"
        info += f"Defense: {self.defense}\n"
        if self.damage[0] == self.damage[1]:
            info += f"Damage: {self.damage[0]}\n"
        else:
            info += f"Damage: {self.damage[0]}-{self.damage[1]}\n"
        info += f"Health: {self.health}\n"
        info += f"Speed: {self.speed}\n"
        if full:
            if self.shots > 0:
                info += f"Shots: {self.shots}\n"
            info += f"Cost: {self.cost}\n"
            info += f"Movement: {self.movement}\n"
            info += f"Growth: {self.growth}\n"
            info += f"Size: {self.size}\n"
            info += f"Source: {self.source_name} v{self.source_version}\n"
            abilities = [str(ab) for ab in self.abilities]
            if len(abilities) > 0:
                info += "Abilities:\n\t" + "\n\t".join(abilities) + "\n"
        return info


class Stack:
    def __init__(self, unit: Unit, count: int = 1):
        if count < 1:
            raise ValueError("Count must be greater than 0!")
        self.unit = unit
        self.count = count
        self.count_base = count

        self.tag = None
        self.position = None
        self.health = None
        self.health_max = None
        self.shots = None
        self.retaliations = None
        self.run_up = 0
        self.strategy = None
        self.extra_turn = False
        self.actions_left = 0

        unit_id = self.unit.id
        REGISTER[unit_id] = REGISTER.get(unit_id, 0) + 1
        self.id_value = REGISTER[unit_id]

        self.states = []
        self.abilities = []

    @property
    def id(self) -> str:
        return f"{self.unit.id}_{self.id_value}"

    @property
    def name(self) -> str:
        name = self.unit.name
        if self.tag is not None:
            name = f"{name}-{self.tag}"
        return name

    @property
    def name_count(self) -> str:
        return f"{self.name}({self.count})"

    @property
    def size(self) -> int:
        return self.unit.size

    @property
    def entity(self) -> UnitEntity:
        return self.unit.entity

    @property
    def speed_base(self) -> int:
        return self.unit.speed

    @property
    def attack_base(self) -> int:
        return self.unit.attack

    @property
    def defense_base(self) -> int:
        return self.unit.defense

    @property
    def damage_base(self) -> tuple[int, int]:
        return self.unit.damage

    @property
    def shots_base(self) -> int:
        return self.unit.shots

    @property
    def luck_base(self) -> int:
        return 0

    @property
    def morale_base(self) -> int:
        if self.is_affected_by_morale():
            return 1
        return 0

    @property
    def health_base(self) -> int:
        return self.unit.health

    @property
    def health_all(self) -> int:
        if self.count <= 0:
            return 0
        return self.health_max * (self.count - 1) + self.health

    @property
    def retaliations_max(self) -> int | str:
        ability = self.get_ability("Retaliations")
        if ability is not None:
            return ability["val"]
        return 1

    @property
    def n_strikes(self) -> int:
        ability = self.get_ability("MultipleStrike")
        if ability is not None:
            return ability["val"]
        return 1

    @property
    def n_shoots(self) -> int:
        ability = self.get_ability("MultipleShoot")
        if ability is not None:
            return ability["val"]
        return 1

    def is_affected_by_morale(self) -> bool:
        return self.unit.entity == UnitEntity.Living

    def is_died(self) -> bool:
        return self.count == 0

    def is_ranged(self) -> bool:
        return self.shots_base > 0

    def is_immune_to_ability(self, ability_name: str) -> bool:
        for immunity in self.get_ability("Immunity", return_all=True):
            if immunity["arg"] == ability_name:
                return True
        return False

    def is_immune_to_effect(self, effect) -> bool:
        if (
                (EffectDomain.Mind in effect.domains) and
                (self.entity in {UnitEntity.Undead, UnitEntity.Unliving, UnitEntity.Mechanical})
        ):
            return True

        for immunity in self.get_ability("Immunity", return_all=True):
            arg = immunity["arg"]

            if isinstance(arg, Filter):
                if isinstance(effect, Effect) and arg.matches(effect):
                    return True
                continue

            if isinstance(effect, str) and arg == effect:
                return True

            if isinstance(effect, Effect) and arg == effect.name:
                return True

        return False

    def has_ability(self, ability_name: str) -> bool:
        return any(ability.name == ability_name for ability in self.abilities)

    def has_state(self, state_name: str) -> bool:
        return any(state.name == state_name for state in self.states)

    def prepare_battle(self):
        self.health_max = self.health_base
        self.health = self.health_max
        self.shots = self.shots_base
        self.abilities = [ability.bind(self.id) for ability in self.unit.abilities]

    def prepare_round(self):
        self.retaliations = self.retaliations_max
        self.extra_turn = False
        self.actions_left = 0

    def apply_damage(self, damage: int) -> int:
        count_before = self.count
        health_total = self.health_all - damage
        if health_total <= 0:
            self.count = 0
            self.health = 0
            return count_before
        health_remain = health_total % self.health_max
        count_remain = health_total // self.health_max + 1
        if health_remain == 0:
            count_remain -= 1
            health_remain = self.health_max
        self.count = count_remain
        self.health = health_remain
        return count_before - self.count

    def kill_units(self, n_units: int) -> int:
        n_killed = min(n_units, self.count)
        self.count -= n_killed
        if self.count <= 0:
            self.count = 0
            self.health = 0
        return n_killed

    def reborn(self, n: int):
        self.count = min(n, self.count_base)
        self.health = self.health_max

    def heal(self, hp: int | None = None) -> int:
        before = self.health
        if hp is None:
            self.health = self.health_max
        else:
            self.health = min(self.health + hp, self.health_max)
        return self.health - before

    def is_damaged(self) -> bool:
        return (self.count < self.count_base) or (self.health < self.health_max)

    def resurrect(self, hp: int | None = None) -> tuple[int, int]:
        health_before = self.health_all
        count_before = self.count

        if hp is None:
            self.count = self.count_base
            self.health = self.health_max
            return self.health_all - health_before, self.count - count_before

        health_total = min(
            self.health_all + hp,
            self.count_base * self.health_max,
        )

        count = health_total // self.health_max
        health = health_total % self.health_max

        if health == 0:
            self.count = count
            self.health = self.health_max if count > 0 else 0
        else:
            self.count = count + 1
            self.health = health

        return self.health_all - health_before, self.count - count_before

    def reduce_health_max(self, percent: int) -> tuple[int, int]:
        health_before = self.health
        health_max_before = self.health_max
        delta = int(np.ceil(self.health_base * percent / 100))
        delta = max(1, delta)
        health_new = self.health_max - delta
        if self.health > delta:
            damage = self.health_max - self.health
            self.health = max(1, health_new - damage)
        else:
            self.health = 1
        self.health_max = health_new
        return health_before, health_max_before

    def decrease_retaliations(self):
        if isinstance(self.retaliations, int):
            self.retaliations -= 1

    def get_ability(self, ability_name: str, return_all: bool = False) -> Ability | list[Ability]:
        abilities = [ability for ability in self.abilities if ability.name == ability_name]
        if return_all:
            return abilities
        return abilities[0] if len(abilities) > 0 else None

    def spell_resistance_probability(self) -> float:
        ability = self.get_ability("SpellResistance")
        if ability:
            return ability["probability"]
        return 0.0

    def __eq__(self, other: "Stack") -> bool:
        return self.id == other.id


def stack_count(unit: Unit, method: str) -> int:
    if method.startswith("fixed"):
        return int(method.replace("fixed", ""))
    elif method == "growth1w":
        return unit.growth
    elif method == "growth1m":
        return 4 * unit.growth
    elif method == "gold10k":
        return int(np.floor(10_000 / unit.cost[Resource.Gold]))
    else:
        raise ValueError(f"Unknown stack count method: '{method}'!")
