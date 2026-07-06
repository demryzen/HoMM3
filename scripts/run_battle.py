"""
Run a single one-vs-one line battle from the command line.

Examples:
    python scripts/run_battle.py "Pikeman" "Ogre" --counts growth1w
    python scripts/run_battle.py "Angel" "Devil" --count1 10 --count2 10 --seed 1
    python scripts/run_battle.py "Cavalier" "Ogre" --counts gold10k --distance 15 --rounds 100

Arguments:
    unit1, unit2: Unit names from the database. Quote names containing spaces.
    --counts: Stack count method passed to homm3.units.stack_count.
        Supported methods are defined by stack_count, currently including:
        fixedN, growth1w, growth1m, gold10k.
    --count1, --count2: Explicit stack counts. Must be provided together.
    --seed: Optional random seed. Defaults to None.
    --distance: Optional initial battle distance. Defaults to None.
    --rounds: Optional round limit. Defaults to None.

Count selection rules:
    Use either --counts or both --count1 and --count2. Do not mix them.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a single HoMM3-like one-vs-one line battle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("unit1", help="First unit name from the database")
    parser.add_argument("unit2", help="Second unit name from the database")
    parser.add_argument("--counts", help="Stack count method for both units")
    parser.add_argument("--count1", type=int, help="Explicit count for unit1")
    parser.add_argument("--count2", type=int, help="Explicit count for unit2")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    parser.add_argument("--distance", type=int, default=None, help="Optional initial battle distance")
    parser.add_argument("--rounds", type=int, default=None, help="Optional round limit")

    args = parser.parse_args()

    has_counts_method = args.counts is not None
    has_explicit_counts = (args.count1 is not None) or (args.count2 is not None)

    if has_counts_method and has_explicit_counts:
        parser.error("Use either --counts or --count1/--count2, not both.")

    if not has_counts_method:
        if args.count1 is None or args.count2 is None:
            parser.error("Provide either --counts or both --count1 and --count2.")

    if args.count1 is not None and args.count1 < 1:
        parser.error("--count1 must be greater than 0.")
    if args.count2 is not None and args.count2 < 1:
        parser.error("--count2 must be greater than 0.")

    return args


def build_stacks(args):
    from homm3.units import Stack, Unit, stack_count

    unit1 = Unit.from_db(args.unit1)
    unit2 = Unit.from_db(args.unit2)

    if args.counts is not None:
        count1 = stack_count(unit1, args.counts)
        count2 = stack_count(unit2, args.counts)
    else:
        count1 = args.count1
        count2 = args.count2

    return Stack(unit1, count=count1), Stack(unit2, count=count2)


def main():
    args = parse_args()

    from homm3.battles.line import LineBattle

    stack1, stack2 = build_stacks(args)

    print(stack1.unit.info(full=True))
    print(stack2.unit.info(full=True))

    battle = LineBattle(
        stack1,
        stack2,
        distance=args.distance,
        rounds=args.rounds,
        seed=args.seed,
        verbose=True,
    )
    battle.run()


if __name__ == "__main__":
    main()
