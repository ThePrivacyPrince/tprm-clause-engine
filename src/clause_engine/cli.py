"""Command-line interface for the TPRM Clause Engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loader import ClauseLoadError, load_library
from .models import ClauseCategory, TierRequirement


def _default_clauses_dir() -> Path:
    cwd = Path.cwd()
    candidate = cwd / "clauses"
    if candidate.exists():
        return candidate
    for parent in cwd.parents:
        candidate = parent / "clauses"
        if candidate.exists():
            return candidate
    return cwd / "clauses"


def cmd_validate(args: argparse.Namespace) -> int:
    clauses_dir = Path(args.clauses_dir) if args.clauses_dir else _default_clauses_dir()
    try:
        library = load_library(clauses_dir)
    except ClauseLoadError as e:
        print(f"VALIDATION FAILED\n{e}", file=sys.stderr)
        return 1

    print("VALIDATION PASSED")
    print(f"  Loaded {len(library.clauses)} clauses from {clauses_dir}")
    by_cat = {}
    for clause in library.clauses:
        by_cat.setdefault(clause.category.value, 0)
        by_cat[clause.category.value] += 1
    for cat, count in sorted(by_cat.items()):
        print(f"  - {cat}: {count}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    clauses_dir = Path(args.clauses_dir) if args.clauses_dir else _default_clauses_dir()
    library = load_library(clauses_dir)
    clauses = library.clauses

    if args.category:
        try:
            cat = ClauseCategory(args.category)
        except ValueError:
            print(f"Invalid category: {args.category}", file=sys.stderr)
            print(f"Valid categories: {', '.join(c.value for c in ClauseCategory)}", file=sys.stderr)
            return 1
        clauses = [c for c in clauses if c.category == cat]

    if args.framework:
        clauses = [
            c for c in clauses
            if any(m.framework.lower() == args.framework.lower() for m in c.framework_mappings)
        ]

    if args.tier:
        tier_attr = args.tier.lower()
        filtered = []
        for c in clauses:
            req = getattr(c.tier_requirements, tier_attr, None)
            if req in (TierRequirement.REQUIRED, TierRequirement.CONDITIONAL):
                filtered.append(c)
        clauses = filtered

    if not clauses:
        print("No clauses match the filter criteria.")
        return 0

    print(f"{len(clauses)} clauses:")
    for c in sorted(clauses, key=lambda x: x.id):
        print(f"  {c.id}  {c.title}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    clauses_dir = Path(args.clauses_dir) if args.clauses_dir else _default_clauses_dir()
    library = load_library(clauses_dir)
    clause = library.by_id(args.clause_id)
    if not clause:
        print(f"Clause not found: {args.clause_id}", file=sys.stderr)
        return 1

    print(f"{clause.id}  {clause.title}")
    print(f"  Category: {clause.category.value}")
    print(f"  Version:  {clause.version}  (updated {clause.last_updated})")
    print(f"  Author:   {clause.author}")
    print()
    print("STANDARD POSITION")
    print(f"  {clause.standard_position.strip()}")
    print()
    print("FALLBACK POSITION")
    print(f"  {clause.fallback_position.strip()}")
    print()
    print("HARD FLOOR")
    print(f"  {clause.hard_floor.strip()}")
    print()
    print("TIER REQUIREMENTS")
    print(f"  Critical:  {clause.tier_requirements.critical.value}")
    print(f"  High:      {clause.tier_requirements.high.value}")
    print(f"  Moderate:  {clause.tier_requirements.moderate.value}")
    print(f"  Low:       {clause.tier_requirements.low.value}")
    print()
    print("FRAMEWORK MAPPINGS")
    for m in clause.framework_mappings:
        print(f"  {m.framework}: {', '.join(m.controls)}")
    if clause.common_pushback:
        print()
        print("COMMON PUSHBACK")
        for p in clause.common_pushback:
            print(f"  Objection: {p.objection}")
            print(f"  Counter:   {p.counter.strip()}")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    clauses_dir = Path(args.clauses_dir) if args.clauses_dir else _default_clauses_dir()
    library = load_library(clauses_dir)

    framework = args.framework
    coverage = {}
    for clause in library.clauses:
        for m in clause.framework_mappings:
            if m.framework.lower() == framework.lower():
                for control in m.controls:
                    coverage.setdefault(control, []).append(clause.id)

    if not coverage:
        print(f"No clauses map to framework: {framework}")
        return 0

    print(f"Framework: {framework}")
    print(f"Controls covered: {len(coverage)}")
    print()
    for control in sorted(coverage):
        clause_ids = ", ".join(coverage[control])
        print(f"  {control:<20}  {clause_ids}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="clause-engine",
        description="Policy-as-Code engine for the TPRM Master IT Clause Library.",
    )
    parser.add_argument("--clauses-dir", help="Path to the clauses directory")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate every clause in the library")
    p_val.set_defaults(func=cmd_validate)

    p_list = sub.add_parser("list", help="List clauses with optional filters")
    p_list.add_argument("--category", help="Filter by category")
    p_list.add_argument("--tier", help="Filter by required tier")
    p_list.add_argument("--framework", help="Filter by framework name")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show full detail for one clause")
    p_show.add_argument("clause_id", help="Clause ID, e.g., DP-001")
    p_show.set_defaults(func=cmd_show)

    p_cov = sub.add_parser("coverage", help="Show framework control coverage")
    p_cov.add_argument("--framework", required=True, help="Framework name")
    p_cov.set_defaults(func=cmd_coverage)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
