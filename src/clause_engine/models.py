"""Schema definitions for the TPRM Clause Engine.

Treats contract clauses as version-controlled, validated data.
Every clause loaded from YAML is checked against these models.
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ClauseCategory(str, Enum):
    DATA_PROTECTION = "data_protection"
    SECURITY_CONTROLS = "security_controls"
    INCIDENT_RESPONSE = "incident_response"
    LIABILITY = "liability"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"


class TierRequirement(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    NOT_APPLICABLE = "not_applicable"
    CONDITIONAL = "conditional"


class FrameworkMapping(BaseModel):
    framework: str = Field(..., min_length=1)
    controls: List[str] = Field(..., min_length=1)


class Pushback(BaseModel):
    objection: str = Field(..., min_length=1)
    counter: str = Field(..., min_length=1)


class TierRequirements(BaseModel):
    critical: TierRequirement
    high: TierRequirement
    moderate: TierRequirement
    low: TierRequirement


CATEGORY_PREFIX = {
    ClauseCategory.DATA_PROTECTION: "DP",
    ClauseCategory.SECURITY_CONTROLS: "SC",
    ClauseCategory.INCIDENT_RESPONSE: "IR",
    ClauseCategory.LIABILITY: "LI",
    ClauseCategory.COMPLIANCE: "CO",
    ClauseCategory.OPERATIONAL: "OP",
}

CLAUSE_ID_PATTERN = re.compile(r"^(DP|SC|IR|LI|CO|OP)-\d{3}$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class Clause(BaseModel):
    id: str = Field(..., description="Format: <CAT>-NNN, e.g., DP-001")
    category: ClauseCategory
    name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    version: str = Field(...)
    last_updated: date
    author: str = Field(..., min_length=1)

    standard_position: str = Field(..., min_length=10)
    fallback_position: str = Field(..., min_length=10)
    hard_floor: str = Field(..., min_length=10)

    common_pushback: List[Pushback] = Field(default_factory=list)
    tier_requirements: TierRequirements
    framework_mappings: List[FrameworkMapping] = Field(..., min_length=1)

    notes: Optional[str] = None

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not CLAUSE_ID_PATTERN.match(v):
            raise ValueError(
                f"Clause ID must match pattern <CAT>-NNN where CAT is one of "
                f"DP, SC, IR, LI, CO, OP and NNN is a 3-digit number. Got: {v}"
            )
        return v

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        if not SEMVER_PATTERN.match(v):
            raise ValueError(f"Version must be semantic (X.Y.Z). Got: {v}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(
                f"Name must be lowercase snake_case (letters, numbers, underscores). Got: {v}"
            )
        return v

    @model_validator(mode="after")
    def validate_id_matches_category(self) -> "Clause":
        expected_prefix = CATEGORY_PREFIX[self.category]
        actual_prefix = self.id.split("-")[0]
        if actual_prefix != expected_prefix:
            raise ValueError(
                f"Clause ID prefix {actual_prefix!r} does not match category "
                f"{self.category.value!r} (expected prefix {expected_prefix!r})"
            )
        return self


class ClauseLibrary(BaseModel):
    clauses: List[Clause]

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "ClauseLibrary":
        ids = [c.id for c in self.clauses]
        seen = set()
        duplicates = []
        for clause_id in ids:
            if clause_id in seen:
                duplicates.append(clause_id)
            seen.add(clause_id)
        if duplicates:
            raise ValueError(f"Duplicate clause IDs found: {duplicates}")
        return self

    def by_id(self, clause_id: str) -> Optional[Clause]:
        for clause in self.clauses:
            if clause.id == clause_id:
                return clause
        return None

    def by_category(self, category: ClauseCategory) -> List[Clause]:
        return [c for c in self.clauses if c.category == category]

    def by_framework(self, framework: str) -> List[Clause]:
        result = []
        for clause in self.clauses:
            for mapping in clause.framework_mappings:
                if mapping.framework.lower() == framework.lower():
                    result.append(clause)
                    break
        return result

    def required_for_tier(self, tier: str) -> List[Clause]:
        tier_attr = tier.lower()
        result = []
        for clause in self.clauses:
            req = getattr(clause.tier_requirements, tier_attr, None)
            if req in (TierRequirement.REQUIRED, TierRequirement.CONDITIONAL):
                result.append(clause)
        return result
