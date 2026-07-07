from itertools import batched

import pytest

from homm3.battles.line import LineBattle
from homm3.db import DataBase
from homm3.units import Stack, Unit, stack_count


def unit_pairs() -> list[tuple[str, str]]:
    names = DataBase.find_units(source_names="hota")["name"].tolist()
    return [pair for pair in batched(names, 2) if len(pair) == 2]


def pair_id(pair: tuple[str, str]) -> str:
    return f"{pair[0]} vs {pair[1]}"


@pytest.mark.parametrize("unit_pair", unit_pairs(), ids=pair_id)
def test_line_battle_runs_between_unit_pair(unit_pair: tuple[str, str]):
    unit1 = Unit.from_db(unit_pair[0])
    unit2 = Unit.from_db(unit_pair[1])
    stack1 = Stack(unit1, count=stack_count(unit1, "growth1w"))
    stack2 = Stack(unit2, count=stack_count(unit2, "growth1w"))

    battle = LineBattle(
        stack1,
        stack2,
        seed=0,
        verbose=False,
        use_morale=False,
        use_luck=False,
        rounds=100,
    )

    battle.run()

    assert battle.round_index <= battle.rounds_max
    assert stack1.count >= 0
    assert stack2.count >= 0
    assert stack1.health >= 0
    assert stack2.health >= 0

    if battle.winner is not None:
        assert battle.winner in (stack1, stack2)
        assert battle.winner.count > 0
