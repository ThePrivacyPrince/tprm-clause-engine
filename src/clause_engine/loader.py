"""Loads YAML clause files into a validated ClauseLibrary."""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import ValidationError

from .models import Clause, ClauseLibrary


class ClauseLoadError(Exception):
    """Raised when a clause file fails to load or validate."""


def load_clause_file(path: Path) -> Clause:
    """Load and validate a single clause YAML file."""
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ClauseLoadError(f"YAML parse error in {path}: {e}") from e

    if raw is None:
        raise ClauseLoadError(f"Empty clause file: {path}")

    try:
        return Clause(**raw)
    except ValidationError as e:
        raise ClauseLoadError(f"Schema validation failed for {path}:\n{e}") from e


def load_library(clauses_dir: Path) -> ClauseLibrary:
    """Walk the clauses directory and load every YAML file."""
    if not clauses_dir.exists():
        raise ClauseLoadError(f"Clauses directory not found: {clauses_dir}")

    clauses: List[Clause] = []
    yaml_files = sorted(clauses_dir.rglob("*.yaml"))

    if not yaml_files:
        raise ClauseLoadError(f"No clause files found under {clauses_dir}")

    errors: List[str] = []
    for path in yaml_files:
        try:
            clauses.append(load_clause_file(path))
        except ClauseLoadError as e:
            errors.append(str(e))

    if errors:
        raise ClauseLoadError(
            "Failed to load one or more clauses:\n" + "\n\n".join(errors)
        )

    return ClauseLibrary(clauses=clauses)
