# HoMM3

Python package for simulating Heroes of Might and Magic 3 creature battles.
It contains unit definitions, battle logic, abilities, effects, simple match runners,
and visualization helpers for comparing battle results.

## Run a Battle

Use `scripts/run_battle.py` to run a single one-vs-one line battle from the command line.

Examples:

```bash
python scripts/run_battle.py "Pikeman" "Ogre" --counts growth1w
python scripts/run_battle.py "Angel" "Devil" --count1 10 --count2 10 --seed 1
python scripts/run_battle.py "Cavalier" "Ogre" --counts gold10k --distance 15 --rounds 100
```

Counts can be provided either with `--counts` using `homm3.units.stack_count()` methods,
or explicitly with both `--count1` and `--count2`.

Optional arguments:

- `--seed` for reproducible randomness
- `--distance` for initial battle distance
- `--rounds` for round limit

## Matches

An example round-robin match workflow is available in `notebooks/run_match.ipynb`.
