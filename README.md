# TPRM Clause Engine

**Policy-as-Code for third-party risk management contract clauses.**

A version-controlled, schema-validated library of IT contract clauses with tier-conditional requirements mapped to NIST 800-53, NIST CSF 2.0, ISO 27001:2022, GDPR, and PCI DSS 4.0. Every clause is a YAML file. Every change goes through pull request review. Continuous integration validates the schema on every commit.

## Why this exists

Most TPRM programs treat the contract clause library as a static Word document. Clauses drift. Reviewers freelance. Audit defensibility erodes between formal review cycles.

This project is the engineering implementation of the continuous control monitoring thesis from my 2023 M.S. capstone, *"Cyber Threats and Partnerships: Tailoring a Third-Party Risk Management Program for PCI DSS Compliance"* (Utica University). The capstone made two arguments. First, that vendor self-attestation through questionnaires is structurally weak; forensic inference using observable evidence is more defensible. Second, that point-in-time audits cannot keep pace with the threat landscape; continuous control monitoring is required to catch material changes between audit cycles.

This engine operationalizes the second argument at the contract layer. Clauses are not artifacts that get reviewed once a year. They are version-controlled code with CI-enforced schema validation, queryable by framework control, tier, and category.

## What's in the library

Each clause is a single YAML file under `clauses/<category>/<id>-<slug>.yaml` containing:

- **Standard position**: the preferred contractual language
- **Fallback position**: the minimum acceptable variation
- **Hard floor**: the position below which the clause cannot be negotiated
- **Tier requirements**: required, preferred, or not applicable across Critical / High / Moderate / Low vendor tiers
- **Framework mappings**: which NIST 800-53, NIST CSF 2.0, ISO 27001, PCI DSS, or GDPR controls the clause supports
- **Common pushback**: typical vendor objections and recommended counter-positions

Categories:

| Category | Code | Examples |
|---|---|---|
| Data Protection | `DP` | Limited purpose processing, subprocessor management |
| Security Controls | `SC` | Information security program, encryption standards |
| Incident Response | `IR` | Breach notification, investigation coordination |
| Liability | `LI` | General liability cap, security incident super-cap |
| Compliance | `CO` | Right to audit, attestation delivery |
| Operational | `OP` | Data return and destruction, transition assistance |

## Quick start

```bash
# Install
git clone https://github.com/ThePrivacyPrince/tprm-clause-engine.git
cd tprm-clause-engine
pip install -e ".[dev]"

# Validate the entire library
clause-engine validate

# List all clauses required for Critical tier vendors
clause-engine list --tier critical

# Show full detail for a single clause
clause-engine show IR-001

# See which NIST 800-53 controls are covered by current clauses
clause-engine coverage --framework "NIST 800-53 Rev 5"
```

## Schema

Clauses are validated by Pydantic models defined in `src/clause_engine/models.py`. The schema enforces:

- Clause IDs match the pattern `<CAT>-NNN` (e.g., `DP-001`)
- Clause ID prefix matches the declared category
- Names are lowercase snake_case
- Versions are semver
- Every clause has at least one framework mapping
- No duplicate IDs across the library

Schema violations fail CI. The library cannot drift.

## Architecture

```
tprm-clause-engine/
├── src/clause_engine/
│   ├── models.py        # Pydantic schema definitions
│   ├── loader.py        # YAML loading and validation
│   └── cli.py           # Command-line interface
├── clauses/
│   ├── data_protection/
│   ├── security_controls/
│   ├── incident_response/
│   ├── liability/
│   ├── compliance/
│   └── operational/
├── tests/
│   └── test_clause_engine.py
└── .github/workflows/
    └── validate.yml     # CI: validates library on every push
```

## How it fits in the broader TPRM platform

This engine is the data backbone for two related tools (in development):

- **Vendor Risk Scoring Engine**: ingests a vendor profile, determines inherent and residual tier with rationale tracking, and uses this clause library to produce tier-conditional contract requirements.
- **Contract Clause Analyzer**: ingests vendor MSAs (PDF), extracts the clauses present, and compares them against this library to produce a gap report mapped to NIST 800-53 SR controls.

Together they form a contract review platform anchored to NIST as the primary framework with ISO 27001 and PCI DSS as supporting context.

## Roadmap

- [ ] Coverage analysis: which NIST controls are addressed across the library
- [ ] Markdown export for human-readable clause summaries
- [ ] Diff tool: show what changed between clause versions
- [ ] Integration with the Vendor Risk Scoring Engine
- [ ] AI vendor addendum clauses (NIST AI RMF, ISO 42001 alignment)

## Research foundation

This project is the engineering implementation of arguments developed in my 2023 M.S. capstone at Utica University. The paper drew on Kellogg et al.'s "Continuous Compliance" (2020) framework to argue that compliance posture must be continuously instrumented rather than periodically inspected. This engine extends that argument into the contract clause domain: clauses are version-controlled, validated, and queryable artifacts, not static documents that drift between reviews.

## License

MIT. See `LICENSE`.

## Author

Irvens Eristil — GRC analyst focused on third-party risk and IT contract review.
[github.com/ThePrivacyPrince](https://github.com/ThePrivacyPrince)
