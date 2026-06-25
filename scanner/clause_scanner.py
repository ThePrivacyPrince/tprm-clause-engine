#!/usr/bin/env python3
"""
clause_scanner.py  —  Clause Engine v2: security/privacy clause linter
======================================================================

Scans a vendor contract (MSA / DPA / order form) against a clause baseline
and produces a redline checklist:

  * MISSING            – none of the clause's signal phrases were found
  * PRESENT (weak)     – clause is present but uses one-sided / weak language
  * PRESENT (verify)   – clause is present but the required value wasn't detected
  * PRESENT (ok)       – clause is present with no flags

It loads `clause-engine-baseline.json` (the tunable baseline), so adding or
editing clauses means editing the JSON, not this code.

USAGE
-----
    python clause_scanner.py contract.pdf
    python clause_scanner.py contract.docx --baseline clause-engine-baseline.json
    python clause_scanner.py contract.txt  --out report     # writes report.md + report.json
    cat contract.txt | python clause_scanner.py -            # read from stdin

Supported inputs: .txt / .md (native), .pdf (needs pdfplumber or pypdf),
.docx (native stdlib fallback — no dependency required).

NOTE ON TUNING
--------------
`red_flags` and `required_value` are starting heuristics. The scanner SURFACES
findings for human review; it never auto-rejects. Expect to tune the baseline
as you run real contracts through it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Severity weighting — drives the overall risk score                          #
# --------------------------------------------------------------------------- #
WEIGHTS = {
    ("missing", "critical"): 10,
    ("missing", "high"): 5,
    ("weak", "critical"): 6,
    ("weak", "high"): 3,
    ("verify", "critical"): 2,
    ("verify", "high"): 1,
}

DIVISION_LABELS = {
    "parks": "Theme Parks", "studios": "Studios", "stream": "Streaming",
    "news": "News", "sports": "Sports", "corp": "Corporate", "all": "All divisions",
}


# --------------------------------------------------------------------------- #
# Text loading                                                                #
# --------------------------------------------------------------------------- #
def load_text(path: str) -> str:
    """Return plain text from a contract file (txt/md/pdf/docx) or stdin ('-')."""
    if path == "-":
        return sys.stdin.read()

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Contract not found: {path}")

    ext = p.suffix.lower()
    if ext in (".txt", ".md", ".text", ""):
        return p.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        return _load_pdf(p)
    if ext == ".docx":
        return _load_docx(p)
    # last resort: try as text
    return p.read_text(encoding="utf-8", errors="ignore")


def _load_pdf(p: Path) -> str:
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(str(p)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            raise RuntimeError(
                "Reading PDFs needs 'pdfplumber' or 'pypdf'. "
                "Install one (pip install pdfplumber) or convert the contract to .txt."
            )
    reader = PdfReader(str(p))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _load_docx(p: Path) -> str:
    """Extract text from .docx with no third-party dependency (stdlib zipfile)."""
    import zipfile
    with zipfile.ZipFile(str(p)) as z:
        parts = [n for n in z.namelist()
                 if n.startswith("word/") and n.endswith(".xml")
                 and ("document" in n or "header" in n or "footer" in n)]
        chunks = []
        for name in parts:
            xml = z.read(name).decode("utf-8", errors="ignore")
            xml = re.sub(r"</w:p>", "\n", xml)        # paragraph breaks
            xml = re.sub(r"<w:tab[^>]*>", "\t", xml)  # tabs
            xml = re.sub(r"<[^>]+>", "", xml)         # strip remaining tags
            chunks.append(xml)
    text = "\n".join(chunks)
    # unescape the handful of XML entities docx uses
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&apos;", "'")):
        text = text.replace(a, b)
    return text


# --------------------------------------------------------------------------- #
# Normalization & matching                                                    #
# --------------------------------------------------------------------------- #
def normalize(text: str) -> str:
    """Lowercase, fold unicode, normalize quotes/dashes/whitespace for matching."""
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")   # zero-width / BOM
    # smart quotes & dashes -> ascii
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u2011", "-")):
        text = text.replace(a, b)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def find_phrase(needle: str, haystack_norm: str) -> bool:
    """True if a (normalized) phrase appears in the normalized contract text."""
    return normalize(needle) in haystack_norm


def snippet(needle: str, raw_text: str, width: int = 70) -> Optional[str]:
    """Return a short context window around the first occurrence of `needle`."""
    norm_doc = normalize(raw_text)
    norm_needle = normalize(needle)
    idx = norm_doc.find(norm_needle)
    if idx == -1:
        return None
    start = max(0, idx - width)
    end = min(len(norm_doc), idx + len(norm_needle) + width)
    frag = norm_doc[start:end].strip()
    return f"...{frag}..."


_VALUE_RE = re.compile(r"(\d+)\s*(hour|day|week|month|year)", re.I)


def value_target(required_value: str) -> Optional[str]:
    """Pull a duration target (e.g. '24 hour') out of a required_value string."""
    m = _VALUE_RE.search(required_value)
    if not m:
        return None
    return f"{m.group(1)} {m.group(2).lower()}"


# --------------------------------------------------------------------------- #
# Findings                                                                     #
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    clause_id: str
    name: str
    status: str            # missing | weak | verify | ok
    severity: str          # critical | high
    crown_jewels: list
    elite_position: str
    evidence: list = field(default_factory=list)
    cross_ref: Optional[str] = None

    @property
    def points(self) -> int:
        return WEIGHTS.get((self.status, self.severity), 0)


def scan_clause(clause: dict, raw_text: str, norm_text: str) -> Finding:
    det = clause.get("detect", {})
    present_if = det.get("present_if", [])
    red_flags = det.get("red_flags", [])
    required = det.get("required_value", "")

    base = dict(
        clause_id=clause["id"], name=clause["name"],
        severity=clause.get("severity", "high"),
        crown_jewels=clause.get("crown_jewels", ["all"]),
        elite_position=clause.get("elite_position", ""),
        cross_ref=clause.get("cross_ref"),
    )

    present = any(find_phrase(p, norm_text) for p in present_if)
    if not present:
        return Finding(status="missing", evidence=["No signal phrase found."], **base)

    # present — now look for weak language and value gaps
    evidence, status = [], "ok"

    hits = [rf for rf in red_flags if find_phrase(rf, norm_text)]
    if hits:
        status = "weak"
        for rf in hits:
            evidence.append(f"weak language: \"{rf}\"  →  {snippet(rf, raw_text)}")

    target = value_target(required) if required else None
    if target and not find_phrase(target, norm_text):
        if status == "ok":
            status = "verify"
        evidence.append(f"required value '{target}' not detected — confirm the contract meets it.")

    if status == "ok":
        matched = next((p for p in present_if if find_phrase(p, norm_text)), "")
        evidence.append(f"present: \"{matched}\"")

    return Finding(status=status, evidence=evidence, **base)


# --------------------------------------------------------------------------- #
# Reporting                                                                    #
# --------------------------------------------------------------------------- #
def grade(score: int, n_clauses: int) -> str:
    """Map a weighted gap score to a letter grade (lower score = better)."""
    per = score / max(n_clauses, 1)
    if per <= 0.3:  return "A"
    if per <= 0.8:  return "B"
    if per <= 1.6:  return "C"
    if per <= 2.6:  return "D"
    return "F"


def summarize(findings: list, baseline: dict) -> dict:
    total = len(findings)
    by_status = {s: [f for f in findings if f.status == s] for s in ("missing", "weak", "verify", "ok")}
    score = sum(f.points for f in findings)
    present = total - len(by_status["missing"])
    # crown-jewel exposure: jewels touched by a missing/weak finding
    exposure: dict[str, list] = {}
    for f in findings:
        if f.status in ("missing", "weak"):
            for j in f.crown_jewels:
                exposure.setdefault(j, []).append(f.clause_id)
    return {
        "total": total, "present": present,
        "coverage_pct": round(100 * present / max(total, 1)),
        "missing": len(by_status["missing"]),
        "weak": len(by_status["weak"]),
        "verify": len(by_status["verify"]),
        "score": score, "grade": grade(score, total),
        "exposure": exposure, "by_status": by_status,
    }


def print_console(findings: list, s: dict) -> None:
    bar = "=" * 64
    print(f"\n{bar}\n  CLAUSE SCAN — REDLINE CHECKLIST\n{bar}")
    print(f"  Coverage : {s['present']}/{s['total']} clauses present  ({s['coverage_pct']}%)")
    print(f"  Gaps     : {s['missing']} missing · {s['weak']} weak · {s['verify']} to verify")
    print(f"  Risk     : score {s['score']}  →  grade {s['grade']}")
    print(bar)

    order = {"missing": 0, "weak": 1, "verify": 2, "ok": 3}
    icon = {"missing": "✗ MISSING ", "weak": "▲ WEAK    ", "verify": "? VERIFY  ", "ok": "✓ OK      "}
    for f in sorted(findings, key=lambda x: (order[x.status], x.severity != "critical", x.clause_id)):
        if f.status == "ok":
            continue  # console focuses on action items; full list is in the report files
        jew = ", ".join(DIVISION_LABELS.get(j, j) for j in f.crown_jewels)
        tag = "CRIT" if f.severity == "critical" else "high"
        print(f"\n  {icon[f.status]} [{tag}] {f.clause_id}  {f.name}")
        print(f"     protects: {jew}")
        if f.cross_ref:
            print(f"     cross-ref: {f.cross_ref}")
        for e in f.evidence:
            print(f"     - {e}")
        if f.status in ("missing", "weak"):
            print(f"     ASK FOR: {f.elite_position}")

    if s["exposure"]:
        print(f"\n{bar}\n  CROWN-JEWEL EXPOSURE (gaps by division)\n{bar}")
        for j, ids in sorted(s["exposure"].items(), key=lambda kv: -len(kv[1])):
            print(f"  {DIVISION_LABELS.get(j, j):14s} {len(ids):2d} open  ({', '.join(ids)})")
    print()


def markdown_report(findings: list, s: dict, contract_name: str) -> str:
    L = [f"# Clause Scan — Redline Checklist", "",
         f"**Contract:** {contract_name}  ",
         f"**Coverage:** {s['present']}/{s['total']} ({s['coverage_pct']}%)  ",
         f"**Gaps:** {s['missing']} missing · {s['weak']} weak · {s['verify']} to verify  ",
         f"**Risk grade:** {s['grade']} (score {s['score']})", ""]

    def block(title: str, status: str):
        items = s["by_status"][status]
        if not items:
            return
        L.append(f"## {title} ({len(items)})\n")
        for f in sorted(items, key=lambda x: x.severity != "critical"):
            jew = ", ".join(DIVISION_LABELS.get(j, j) for j in f.crown_jewels)
            sev = "🔴 die-on-it" if f.severity == "critical" else "🟠 high"
            L.append(f"### {f.clause_id} — {f.name}  ({sev})")
            L.append(f"- **Protects:** {jew}")
            if f.cross_ref:
                L.append(f"- **Cross-reference:** {f.cross_ref}")
            for e in f.evidence:
                L.append(f"- {e}")
            if status in ("missing", "weak"):
                L.append(f"- **Ask for:** {f.elite_position}")
            L.append("")

    block("✗ Missing — add these", "missing")
    block("▲ Present but weak — renegotiate", "weak")
    block("? Verify the value", "verify")
    block("✓ Present and clean", "ok")

    if s["exposure"]:
        L.append("## Crown-jewel exposure\n")
        for j, ids in sorted(s["exposure"].items(), key=lambda kv: -len(kv[1])):
            L.append(f"- **{DIVISION_LABELS.get(j, j)}** — {len(ids)} open: {', '.join(ids)}")
        L.append("")
    L.append("---\n*Generated by clause_scanner.py · findings are advisory — review before redlining.*")
    return "\n".join(L)


def json_report(findings: list, s: dict, contract_name: str) -> dict:
    return {
        "contract": contract_name,
        "summary": {k: s[k] for k in
                    ("total", "present", "coverage_pct", "missing", "weak", "verify", "score", "grade")},
        "crown_jewel_exposure": s["exposure"],
        "findings": [
            {"id": f.clause_id, "name": f.name, "status": f.status, "severity": f.severity,
             "crown_jewels": f.crown_jewels, "cross_ref": f.cross_ref,
             "evidence": f.evidence, "ask_for": f.elite_position}
            for f in findings
        ],
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def run(contract_path: str, baseline_path: str) -> tuple[list, dict, str]:
    baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    clauses = baseline["clauses"]
    raw = load_text(contract_path)
    norm = normalize(raw)
    findings = [scan_clause(c, raw, norm) for c in clauses]
    s = summarize(findings, baseline)
    name = "stdin" if contract_path == "-" else Path(contract_path).name
    return findings, s, name


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Scan a contract against the clause baseline.")
    ap.add_argument("contract", help="path to contract (.txt/.md/.pdf/.docx) or '-' for stdin")
    ap.add_argument("--baseline", default=str(here / "clause-engine-baseline.json"),
                    help="path to clause-engine-baseline.json")
    ap.add_argument("--out", help="write <out>.md and <out>.json reports")
    ap.add_argument("--quiet", action="store_true", help="suppress console output")
    args = ap.parse_args(argv)

    findings, s, name = run(args.contract, args.baseline)

    if not args.quiet:
        print_console(findings, s)

    if args.out:
        Path(f"{args.out}.md").write_text(markdown_report(findings, s, name), encoding="utf-8")
        Path(f"{args.out}.json").write_text(
            json.dumps(json_report(findings, s, name), indent=2), encoding="utf-8")
        print(f"  → wrote {args.out}.md and {args.out}.json\n")

    # exit non-zero if any critical clause is missing — handy for CI / pipelines
    return 1 if any(f.status == "missing" and f.severity == "critical" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
