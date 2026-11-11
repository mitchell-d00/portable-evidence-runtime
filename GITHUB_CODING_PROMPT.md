# Repository development instructions for a coding assistant

**Repository:** `portable-evidence-runtime`\
**Research author:** Mitchell D. McPhetridge\
**Foundational paper:** `core-papers/Portable_Evidence_Runtime.md` (`paper/` contains generated compatibility copies)

## Mission

Maintain and extend an offline-first, portable evidence runtime answering one research question:

> If memory, rules, verification, and software can travel together, why require a particular notebook, cloud account, or AI provider to reconstruct the system?

Do not replace this objective with a chatbot, remote API wrapper, cloud notebook dependency, or opaque hosted service. Keep the included paper unchanged unless explicitly instructed to revise its text; all three paper formats must remain substantively consistent after an authorized revision.

## Read first

Read `README.md`, `paper/Portable_Evidence_Runtime.md`, `experiment/PROTOCOL.md`, `docs/THREAT_MODEL.md`, `src/per/core.py`, `web/source_runtime.js`, `src/engine.js`, and the test fixtures. Explain the difference between the `PER-LEDGER-1` local authoring format and `portable-evidence-capsule/1` strict verification format; do not silently merge their representations or claim equivalence.

## Implementation contract

1. Preserve two independent, accessible entry points: root `index.html` for local authoring and `web/index.html` for pinned-capsule inspection. They must open as files without network access, login, external JavaScript, fonts, remote assets, or provider keys. A single-file application may use browser-provided APIs.
2. Keep the strict engine exact-key, deterministic, and fail-closed. Do not claim natural-language understanding. Preserve the explicit statuses `supported`, `ambiguous`, `not_in_corpus`, `invalid_key`, and `integrity_error`.
3. Require a separately supplied matching expected root for **supported** answers in strict browser mode. A rehashed capsule with a new root may be internally consistent but must not be treated as authenticated by an untrusted self-declared hash.
4. Validate schema, record order, lineage, policy, digest, uniqueness, revision, and eligibility. Never silently repair invalid imported bytes or promote an ineligible record.
5. Preserve evidence: a supported return identifies the exact record and content or record digest. Do not generate new unsupported source claims.
6. All fixtures must be explicitly synthetic and have known outputs. Never modify an original source fixture in place without assigning a new experiment ID and regenerating its independently retained root.
7. Use standards-based, auditable mechanisms; keep source code readable and deterministic. No network calls in core local operations.
8. Any new signing mode must specify signer trust, key distribution, revocation, and the threat model; do not treat hash consistency as a signature.
9. Keep the usability of touch and desktop browsers. Export/import must use ordinary files and make private data handling explicit.
10. Maintain changelog and reproduce the result JSON. Do not report a test as having passed unless executed at the exact revision being reported.

## Required work items

**Phase 1: audit the frozen reference.** Run all tests and the browser offline probe. Check DOM functionality, size limits, data mutation rejection, hash parity, file import, accessibility labels, UTF-8 and Unicode, distinct origins, revision handling, and failure messages. File issues for any discrepancy rather than concealing it.

**Phase 2: improve local transfer.** Build a self-describing export package that includes content files, a machine-readable manifest, policy version, digest ledger, reproducibility command, and a mechanism for carrying a separately trusted expected root. The package must distinguish `built`, `exported`, `received`, `verified`, `accepted`, and `refused` states. Offer local ZIP export/import if it can be implemented without remote runtime dependencies; otherwise specify the bound and preserve the plain JSON path.

**Phase 3: harden evidence control.** Add explicit source scope, active/retired/blocked status, revision lineage, conflict handling, derivative parent pins, schema version migration, deterministic exception categorization, and corruption detection. Only accept a feature after a corresponding adversarial test demonstrates both allowed and denied behavior.

**Phase 4: instrument the experiment.** Implement the controlled C0/C1/C2/C3 test conditions described in `experiment/PROTOCOL.md`. Record transfer success, external dependencies, actual network requests, human interventions, elapsed recovery time, exact answer/refusal statuses, precision, and coverage. Produce portable JSON and human-readable result summaries. Do **not** claim an independent comparison has been performed before it actually has.

**Phase 5: browser and platform parity.** Test offline operation on Chromium, Firefox, WebKit, mobile browsers where possible, and fresh-profile `file://` use. Enumerate unsupported APIs, denied storage, permission differences, and trust-anchor handling. Report each platform rather than generalizing from one.

## Local commands and acceptance gate

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_browser_core.cjs
node tests/test_authoring_core.cjs
python3 scripts/run_experiment.py
python3 tools/build.py --check
python3 scripts/verify_release.py
```

A change is acceptable only when it preserves or deliberately versions the schema; core operations remain local; corruption, conflicts and unanchored substitutions remain refusals; tests and real browser trials are reported with their limitations; and README, experiment protocol, and paper are not contradicted by the implementation.

## Final development output

Return a concise commit summary, file list, executed commands with exact pass/fail counts, observed platform versions, unresolved limitations, and links to generated results. Do not invent evidence, publication status, security certification, or production readiness.
