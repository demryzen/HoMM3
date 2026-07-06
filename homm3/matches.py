import json
from abc import ABC, abstractmethod
from copy import deepcopy
from itertools import permutations
from pathlib import Path

import numpy as np
from tqdm import tqdm

from homm3.battles.line import LineBattle
from homm3.units import Stack


class Match(ABC):
    def __init__(self, stacks: list[Stack], battle_cls=LineBattle, battle_kwargs: dict | None = None):
        self.stacks = stacks
        self.battle_cls = battle_cls
        self.battle_kwargs = battle_kwargs or {}
        self.results = []

    @abstractmethod
    def run(self, path: str | Path, n_runs: int = 1, show_progress: bool = True, seed: int | None = None) -> dict:
        pass

    def _run_battle(self, stack1: Stack, stack2: Stack, seed: int | None = None) -> str | None:
        stack1 = deepcopy(stack1)
        stack2 = deepcopy(stack2)

        battle_kwargs = {"verbose": False}
        battle_kwargs.update(self.battle_kwargs)
        if seed is not None:
            battle_kwargs["seed"] = seed

        battle = self.battle_cls(stack1, stack2, **battle_kwargs)
        battle.run()

        if battle.winner is None:
            return None
        if battle.winner.id == stack1.id:
            return "stack1"
        if battle.winner.id == stack2.id:
            return "stack2"
        return None

    def _stacks_result(self, stack_ids: dict[int, str]) -> dict:
        return {
            stack_ids[id(stack)]: {
                "name": stack.name,
                "count": stack.count_base,
                "home": str(stack.unit.home),
            }
            for stack in self.stacks
        }

    def _save(self, path: str | Path, data: dict) -> dict:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return data


class RoundRobinMatch(Match):
    name = "RoundRobinMatch"

    def run(self, path: str | Path, n_runs: int = 1, show_progress: bool = True, seed: int | None = None) -> dict:
        self.results = []
        total = len(self.stacks) * (len(self.stacks) - 1) * n_runs
        stack_ids = {id(stack): f"stack{index}" for index, stack in enumerate(self.stacks, start=1)}

        rng = np.random.default_rng(seed) if seed is not None else None

        with tqdm(total=total, desc="Battles", disable=not show_progress) as progress:
            for stack1, stack2 in permutations(self.stacks, 2):
                progress.set_description(f"{stack1.name} vs {stack2.name}")
                result = self._run_pair(
                    stack1=stack1,
                    stack2=stack2,
                    stack1_id=stack_ids[id(stack1)],
                    stack2_id=stack_ids[id(stack2)],
                    n_runs=n_runs,
                    rng=rng,
                    progress=progress,
                )
                self.results.append(result)

        data = {
            "match": self.name,
            "stacks": self._stacks_result(stack_ids),
            "settings": {
                "n_runs": n_runs,
                "seed": seed,
                "battle": self.battle_cls.__name__,
                "battle_kwargs": self.battle_kwargs,
            },
            "results": self.results,
        }

        return self._save(path, data)

    def _run_pair(
        self,
        stack1: Stack,
        stack2: Stack,
        stack1_id: str,
        stack2_id: str,
        n_runs: int,
        rng: np.random.Generator | None,
        progress,
    ) -> dict:
        wins = {"stack1": 0, "stack2": 0, "draw": 0}

        for _ in range(n_runs):
            battle_seed = int(rng.integers(0, 2 ** 32 - 1)) if rng is not None else None
            winner = self._run_battle(stack1, stack2, seed=battle_seed)
            progress.update()

            if winner is None:
                wins["draw"] += 1
                continue

            wins[winner] += 1

        return {
            stack1_id: wins["stack1"],
            stack2_id: wins["stack2"],
            "draw": wins["draw"],
        }
