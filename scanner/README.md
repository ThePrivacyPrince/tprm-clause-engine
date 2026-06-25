# Clause Scanner (Clause Engine v2)

A standalone security/privacy **clause linter** for vendor contracts. Point it at an
MSA, DPA, or order form and it produces a redline checklist: which protective clauses
are missing, which are present but weak, and which need a value confirmed before sign-off.

This is the contract-analysis companion to the policy-as-code clause library in the
[repository root](../README.md). Where the root project *defines* the standard positions
as version-controlled YAML, this tool *reads a vendor's contract* and grades it against a
tunable baseline.

> **Advisory only.** The scanner surfaces findings for human review. It never auto-rejects
> a contract — every flag is a starting point for a redline, not a verdict.

## How it works

1. **Load** the contract text (`.txt`/`.md` natively, `.pdf` and `.docx` when the optional
   readers are available).
2. **Normalize** it — lowercase, fold unicode, flatten smart quotes/dashes/whitespace — so
   matching is robust to formatting noise.
3. **Scan** each clause in `clause-engine-baseline.json` for:
   - `present_if` — signal phrases that show the clause exists
   - `red_flags` — one-sided / weak language to flag even when the clause is present
   - `required_value` — a specific value (e.g. a 24-hour breach window) to confirm
4. **Grade** the gaps into a weighted risk score and an A–F letter grade, plus a
   crown-jewel exposure view (which business divisions each gap touches).

Every finding lands in one of four states:

| Status | Meaning |
|---|---|
| `✗ MISSING` | No signal phrase for the clause was found |
| `▲ WEAK` | Clause is present but uses weak / one-sided language |
| `? VERIFY` | Clause is present but the required value wasn't detected |
| `✓ OK` | Clause is present with no flags |

## Usage

```bash
# Scan a contract and print the redline checklist to the console
python clause_scanner.py examples/sample_contract.txt

# Write Markdown + JSON reports (report.md / report.json)
python clause_scanner.py examples/sample_contract.txt --out report

# Use a different baseline
python clause_scanner.py contract.pdf --baseline clause-engine-baseline.json

# Read from stdin
cat contract.txt | python clause_scanner.py -
```

The scanner exits non-zero if any **critical** clause is missing, so it can gate a
CI pipeline or pre-signature check.

### Optional dependencies

`.txt`/`.md`/`.docx` need nothing beyond the standard library. For `.pdf` contracts,
install one PDF reader:

```bash
pip install pdfplumber   # or: pip install pypdf
```

## The baseline

`clause-engine-baseline.json` is the tunable rulebook — 28 clauses across security
(`SEC-01`…`SEC-14`) and privacy/DPA (`DPA-01`…`DPA-14`), each mapped to frameworks
(NIST 800-53, ISO 27001, GDPR, CCPA, PCI DSS, VPPA, TPN) and tagged with the crown-jewel
divisions it protects.

Adding or tightening a clause means editing the JSON, not the code. The `red_flags` and
`required_value` fields are deliberately starting heuristics — expect to tune them as real
contracts run through the scanner.

## Worked example

`examples/sample_contract.txt` is an intentionally weak vendor agreement.
`examples/sample_report.md` is the redline checklist the scanner produces from it:

```
Coverage : 12/28 clauses present  (43%)
Gaps     : 16 missing · 6 weak · 0 to verify
Risk     : score 137  →  grade F
```

Regenerate it yourself:

```bash
python clause_scanner.py examples/sample_contract.txt --out examples/sample_report
```

## Files

| File | Purpose |
|---|---|
| `clause_scanner.py` | The linter — loading, normalization, scanning, reporting |
| `clause-engine-baseline.json` | The 28-clause baseline (edit this to tune) |
| `examples/sample_contract.txt` | A deliberately weak sample contract |
| `examples/sample_report.md` | The checklist generated from the sample |
