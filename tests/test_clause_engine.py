"""
Test suite for the TPRM Clause Engine.

Coverage:
- Schema validation (valid clauses load, invalid ones fail)
- Loader (real library loads, malformed files raise structured errors)
- Library queries (by_id, by_category, by_framework, required_for_tier)
- Real library content (sanity checks on the shipped clauses)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from clause_engine import (
    Clause,
    ClauseCategory,
    ClauseLibrary,
    ClauseLoadError,
    FrameworkMapping,
    Pushback,
    TierRequirement,
    TierRequirements,
    load_clause_file,
    load_library,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUSES_DIR = REPO_ROOT / "clauses"


# ---------- Fixtures ----------


@pytest.fixture
def valid_clause_dict() -> dict:
    """A minimal valid clause as a Python dict."""
    return {
        "id": "DP-999",
        "category": "data_protection",
        "name": "test_clause",
        "title": "Test Clause",
        "version": "1.0.0",
        "last_updated": "2026-05-06",
        "author": "Test Author",
        "standard_position": "This is the standard position with enough length.",
        "fallback_position": "This is fallback long enough.",
        "hard_floor": "Hard floor minimum length.",
        "tier_requirements": {
            "critical": "required",
            "high": "required",
            "moderate": "preferred",
            "low": "not_applicable",
        },
        "framework_mappings": [
            {"framework": "NIST 800-53 Rev 5", "controls": ["SR-3"]},
        ],
    }


# ---------- Schema validation ----------


class TestClauseSchema:
    def test_valid_clause_parses(self, valid_clause_dict):
        clause = Clause(**valid_clause_dict)
        assert clause.id == "DP-999"
        assert clause.category == ClauseCategory.DATA_PROTECTION

    def test_missing_required_field_raises(self, valid_clause_dict):
        del valid_clause_dict["title"]
        with pytest.raises(ValidationError):
            Clause(**valid_clause_dict)

    def test_invalid_id_pattern_raises(self, valid_clause_dict):
        valid_clause_dict["id"] = "invalid-id"
        with pytest.raises(ValidationError):
            Clause(**valid_clause_dict)

    def test_invalid_version_pattern_raises(self, valid_clause_dict):
        valid_clause_dict["version"] = "1.0"  # missing patch
        with pytest.raises(ValidationError):
            Clause(**valid_clause_dict)

    def test_unknown_category_raises(self, valid_clause_dict):
        valid_clause_dict["category"] = "made_up_category"
        with pytest.raises(ValidationError):
            Clause(**valid_clause_dict)

    def test_id_prefix_must_match_category(self, valid_clause_dict):
        # DP- prefix with category=incident_response should fail
        valid_clause_dict["category"] = "incident_response"
        with pytest.raises(ValidationError, match="prefix"):
            Clause(**valid_clause_dict)

    def test_pushback_structure(self, valid_clause_dict):
        valid_clause_dict["common_pushback"] = [
            {"objection": "Vendor refuses X", "counter": "Counter with Y"},
        ]
        clause = Clause(**valid_clause_dict)
        assert len(clause.common_pushback) == 1
        assert clause.common_pushback[0].objection == "Vendor refuses X"


class TestClauseLibrary:
    def _make_clause(self, clause_id: str, category: str = "data_protection") -> Clause:
        prefix = clause_id.split("-")[0]
        cat = ClauseCategory(category)
        return Clause(
            id=clause_id,
            category=cat,
            name=f"clause_{clause_id.lower().replace('-', '_')}",
            title=f"Test {clause_id}",
            version="1.0.0",
            last_updated=date(2026, 5, 6),
            author="Test",
            standard_position="A standard position long enough to validate.",
            fallback_position="A fallback position.",
            hard_floor="A hard floor of minimum length.",
            tier_requirements=TierRequirements(
                critical=TierRequirement.REQUIRED,
                high=TierRequirement.REQUIRED,
                moderate=TierRequirement.PREFERRED,
                low=TierRequirement.NOT_APPLICABLE,
            ),
            framework_mappings=[
                FrameworkMapping(framework="NIST 800-53 Rev 5", controls=["SR-3"]),
            ],
        )

    def test_duplicate_clause_ids_rejected(self):
        c1 = self._make_clause("DP-001")
        c2 = self._make_clause("DP-001")
        with pytest.raises(ValidationError, match="Duplicate clause IDs"):
            ClauseLibrary(clauses=[c1, c2])

    def test_by_id_returns_clause(self):
        c = self._make_clause("DP-001")
        lib = ClauseLibrary(clauses=[c])
        assert lib.by_id("DP-001") == c
        assert lib.by_id("missing") is None

    def test_by_category_filters(self):
        c = self._make_clause("DP-001")
        lib = ClauseLibrary(clauses=[c])
        assert lib.by_category(ClauseCategory.DATA_PROTECTION) == [c]
        assert lib.by_category(ClauseCategory.LIABILITY) == []

    def test_by_framework_case_insensitive(self):
        c = self._make_clause("DP-001")
        lib = ClauseLibrary(clauses=[c])
        assert lib.by_framework("NIST 800-53 Rev 5") == [c]
        assert lib.by_framework("nist 800-53 rev 5") == [c]
        assert lib.by_framework("ISO 27001:2022") == []

    def test_required_for_tier(self):
        c = self._make_clause("DP-001")
        lib = ClauseLibrary(clauses=[c])
        assert lib.required_for_tier("critical") == [c]
        assert lib.required_for_tier("low") == []


# ---------- Loader against the real library ----------


class TestLoader:
    def test_real_library_loads(self):
        """The actual clauses directory must always validate."""
        library = load_library(CLAUSES_DIR)
        assert len(library.clauses) > 0
        categories = {c.category for c in library.clauses}
        # All six categories should be represented
        assert categories == set(ClauseCategory)

    def test_missing_directory_raises(self, tmp_path):
        with pytest.raises(ClauseLoadError, match="not found"):
            load_library(tmp_path / "does-not-exist")

    def test_empty_directory_raises(self, tmp_path):
        with pytest.raises(ClauseLoadError, match="No clause files"):
            load_library(tmp_path)

    def test_malformed_yaml_raises(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(": this is not valid yaml :::")
        with pytest.raises(ClauseLoadError):
            load_library(tmp_path)

    def test_invalid_clause_raises(self, tmp_path, valid_clause_dict):
        del valid_clause_dict["title"]
        bad = tmp_path / "missing-title.yaml"
        bad.write_text(yaml.safe_dump(valid_clause_dict))
        with pytest.raises(ClauseLoadError) as exc_info:
            load_library(tmp_path)
        assert "missing-title.yaml" in str(exc_info.value)

    def test_load_single_file(self):
        sample = CLAUSES_DIR / "data_protection" / "DP-001-limited-purpose-processing.yaml"
        clause = load_clause_file(sample)
        assert clause.id == "DP-001"
        assert clause.category == ClauseCategory.DATA_PROTECTION


# ---------- Real library content sanity checks ----------


class TestLibraryContent:
    @pytest.fixture(scope="class")
    def library(self) -> ClauseLibrary:
        return load_library(CLAUSES_DIR)

    def test_breach_notification_exists(self, library):
        clause = library.by_id("IR-001")
        assert clause is not None
        assert clause.category == ClauseCategory.INCIDENT_RESPONSE

    def test_breach_notification_required_at_all_tiers(self, library):
        clause = library.by_id("IR-001")
        assert clause.tier_requirements.critical == TierRequirement.REQUIRED
        assert clause.tier_requirements.high == TierRequirement.REQUIRED
        assert clause.tier_requirements.moderate == TierRequirement.REQUIRED
        assert clause.tier_requirements.low == TierRequirement.REQUIRED

    def test_nist_sr_family_has_mappings(self, library):
        nist_clauses = library.by_framework("NIST 800-53 Rev 5")
        assert len(nist_clauses) >= 5

    def test_critical_tier_has_required_clauses(self, library):
        critical = library.required_for_tier("critical")
        assert len(critical) >= 5

    def test_all_clauses_have_pushback_or_notes(self, library):
        """Every clause should have at least pushback guidance or notes."""
        for clause in library.clauses:
            assert (
                clause.common_pushback or clause.notes
            ), f"{clause.id} has no pushback or notes"

    def test_no_duplicate_clause_ids_in_library(self, library):
        ids = [c.id for c in library.clauses]
        assert len(ids) == len(set(ids))
