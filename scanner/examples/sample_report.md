# Clause Scan — Redline Checklist

**Contract:** sample_contract.txt  
**Coverage:** 12/28 (43%)  
**Gaps:** 16 missing · 6 weak · 0 to verify  
**Risk grade:** F (score 137)

## ✗ Missing — add these (16)

### SEC-01 — Information Security Requirements / Security Exhibit  (🔴 die-on-it)
- **Protects:** All divisions
- No signal phrase found.
- **Ask for:** Tie the exhibit to a named standard (ISO 27001 / SOC 2 / NIST) so 'reasonable security' is a measurable bar with evidence, not an argument.

### SEC-07 — Limitation of Liability - breach carve-out  (🔴 die-on-it)
- **Protects:** All divisions
- No signal phrase found.
- **Ask for:** Carve breach/confidentiality/IP liability out of the general cap. The most-fought clause in any security negotiation.

### SEC-11 — Data Processing Addendum (DPA)  (🔴 die-on-it)
- **Protects:** Streaming, Corporate
- No signal phrase found.
- **Ask for:** For streaming/ad-tech, embed VPPA-aware terms barring disclosure of viewing data and unconsented pixel/tag deployment.

### DPA-02 — No-Sale / No Secondary Use  (🔴 die-on-it)
- **Protects:** Streaming
- No signal phrase found.
- **Ask for:** Explicit 'shall not sell or share' + 'no use beyond this relationship' + a ban on training the vendor's products/AI. Non-negotiable for ad-tech.

### DPA-10 — Cross-Border Transfer Mechanisms  (🔴 die-on-it)
- **Protects:** Streaming, Corporate
- No signal phrase found.
- **Ask for:** Default to data residency. Where transfers are needed, attach current SCCs plus UK/Swiss addenda, and state SCCs override on conflict.

### DPA-13 — 24/7 Security Contact & 24-Hour Breach Notice  (🔴 die-on-it)
- **Protects:** Corporate, Streaming
- **Cross-reference:** SEC-03
- No signal phrase found.
- **Ask for:** Hold the 24-hour line, the named 24/7 contact, and the gag on third-party disclosure. This is the clause that rewrites the FBCS 5-month ending.

### SEC-09 — Cyber Insurance  (🟠 high)
- **Protects:** All divisions
- No signal phrase found.
- **Ask for:** Set coverage minimums proportional to data sensitivity, require certificates, and notice of any lapse.

### SEC-10 — Compliance with Laws + Framework Flowdown  (🟠 high)
- **Protects:** Theme Parks, Studios
- No signal phrase found.
- **Ask for:** Name the exact standard and evidence cadence (annual AOC, current TPN status). 'Comply with applicable laws' alone is unenforceable.

### SEC-14 — Business Continuity / Availability SLA  (🟠 high)
- **Protects:** Sports
- No signal phrase found.
- **Ask for:** Set uptime SLAs with real financial penalties, require tested failover, and add heightened obligations during marquee live-event windows.

### DPA-01 — Purpose Limitation & Standard of Processing  (🟠 high)
- **Protects:** Streaming, Corporate
- No signal phrase found.
- **Ask for:** Define the permitted purpose narrowly in the contract and require processing strictly on documented instructions. Anything outside is a breach.

### DPA-03 — Confidentiality & Personnel Reliability  (🟠 high)
- **Protects:** Studios, News
- No signal phrase found.
- **Ask for:** Confidentiality surviving termination, role-based least-privilege access, and background checks for anyone touching sensitive content or source material.

### DPA-04 — Subprocessor Approval & Notice  (🟠 high)
- **Protects:** Streaming, Corporate
- **Cross-reference:** SEC-06
- No signal phrase found.
- **Ask for:** Keep approval prospective and specific: name, location, exact processing scope per subprocessor. A website list is not approval.

### DPA-07 — Deletion Verification  (🟠 high)
- **Protects:** Streaming
- No signal phrase found.
- **Ask for:** Require written confirmation of deletion per request. An unverified deletion is the same regulatory exposure as no deletion.

### DPA-08 — Data Protection Impact Assessment (DPIA)  (🟠 high)
- **Protects:** Streaming, Theme Parks
- No signal phrase found.
- **Ask for:** Require DPIA cooperation for any new high-risk processing - especially biometric or children's data - before go-live, not after a regulator asks.

### DPA-12 — Compliance Demonstration & Monitoring  (🟠 high)
- **Protects:** All divisions
- No signal phrase found.
- **Ask for:** Tie monitoring to a 12-month cadence and require the audit report, not just an assertion. Reserve a right to remediate unauthorized use.

### DPA-14 — Accuracy of Representations  (🟠 high)
- **Protects:** All divisions
- No signal phrase found.
- **Ask for:** Keep an explicit truthfulness rep so a false questionnaire answer or stale attestation is a breach, not just an awkward conversation.

## ▲ Present but weak — renegotiate (6)

### SEC-02 — Right to Audit / Assessment  (🔴 die-on-it)
- **Protects:** Studios, Corporate
- weak language: "no more than once per year"  →  ...3. audit. customer shall have the right to audit vendor's compliance no more than once per year, upon reasonable notice. vendor may provide a summary report in lieu...
- weak language: "at vendor's sole discretion"  →  ...tice. vendor may provide a summary report in lieu of an on-site audit at vendor's sole discretion. 4. subcontractors. vendor may engage subcontractors in its discretio...
- **Ask for:** Accept SOC 2 / TPN to move fast, but reserve a direct audit on a security event or material change. Never give that right away entirely.

### SEC-03 — Security Incident & Breach Notification  (🔴 die-on-it)
- **Protects:** Corporate, Streaming
- weak language: "as soon as practicable"  →  ...ification. vendor will notify customer of a confirmed security breach as soon as practicable, and in any event within 72 hours of confirmation. 7. insurance. vend...
- weak language: "72 hours"  →  ...irmed security breach as soon as practicable, and in any event within 72 hours of confirmation. 7. insurance. vendor maintains insurance as it deems...
- required value '24 hour' not detected — confirm the contract meets it.
- **Ask for:** Demand notice within 24-72h of DISCOVERY (not 'confirmation'), defined triggers, and a ban on third-party disclosure without sign-off.

### SEC-04 — Data Return & Secure Destruction  (🔴 die-on-it)
- **Protects:** Corporate
- weak language: "may retain"  →  ...on, vendor will return or destroy customer data, provided that vendor may retain archival copies as required by its internal retention policy. 11. pen...
- weak language: "archival copies"  →  ...will return or destroy customer data, provided that vendor may retain archival copies as required by its internal retention policy. 11. penetration testing...
- **Ask for:** Require certified destruction within a fixed window post-termination, with written attestation. The exact gap FBCS left open.

### SEC-05 — Data Retention & Purpose Limitation  (🟠 high)
- **Protects:** Streaming, Corporate
- weak language: "to improve its services"  →  ...of data. vendor may process customer data to provide the services and to improve its services and develop new products. 6. breach notification. vendor will notify...
- **Ask for:** Bind use to the stated service only, ban product/AI training on your data, and require deletion on a defined schedule.

### SEC-06 — Subcontractor / Fourth-Party Flowdown  (🟠 high)
- **Protects:** Streaming, Studios
- weak language: "may engage subcontractors"  →  ...on-site audit at vendor's sole discretion. 4. subcontractors. vendor may engage subcontractors in its discretion to perform portions of the services. 5. use of data...
- weak language: "in its discretion"  →  ...sole discretion. 4. subcontractors. vendor may engage subcontractors in its discretion to perform portions of the services. 5. use of data. vendor may proce...
- **Ask for:** Require prior written approval and full flowdown; the vendor stays liable for its subs (the Anodot fourth-party lesson).

### DPA-05 — Consumer Rights / DSAR Assistance  (🟠 high)
- **Protects:** Streaming, Corporate
- weak language: "reasonable assistance"  →  ...ity scanning periodically. 12. consumer requests. vendor will provide reasonable assistance with consumer privacy requests....
- required value '10 day' not detected — confirm the contract meets it.
- **Ask for:** Pin the assistance SLA to 10 days and require the vendor to forward any consumer request or complaint immediately, not sit on it.

## ✓ Present and clean (6)

### SEC-08 — Indemnification  (🟠 high)
- **Protects:** Streaming, Corporate
- present: "indemnification"

### SEC-12 — Access Control & Remote Access  (🟠 high)
- **Protects:** Theme Parks, Corporate
- present: "least privilege"

### SEC-13 — Vulnerability Management & Pen Testing  (🟠 high)
- **Protects:** All divisions
- present: "vulnerability"

### DPA-06 — DSAR Audit & Records  (🟠 high)
- **Protects:** Streaming, Corporate
- present: "consumer request"

### DPA-09 — Data Accuracy Notification  (🟠 high)
- **Protects:** Corporate, Streaming
- present: "notify"

### DPA-11 — Written Information Security Plan (WISP)  (🟠 high)
- **Protects:** All divisions
- present: "written information security"

## Crown-jewel exposure

- **Streaming** — 12 open: SEC-03, SEC-05, SEC-06, SEC-11, DPA-01, DPA-02, DPA-04, DPA-05, DPA-07, DPA-08, DPA-10, DPA-13
- **Corporate** — 10 open: SEC-02, SEC-03, SEC-04, SEC-05, SEC-11, DPA-01, DPA-04, DPA-05, DPA-10, DPA-13
- **All divisions** — 5 open: SEC-01, SEC-07, SEC-09, DPA-12, DPA-14
- **Studios** — 4 open: SEC-02, SEC-06, SEC-10, DPA-03
- **Theme Parks** — 2 open: SEC-10, DPA-08
- **Sports** — 1 open: SEC-14
- **News** — 1 open: DPA-03

---
*Generated by clause_scanner.py · findings are advisory — review before redlining.*