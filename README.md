# Portable Evidence Runtime

**Memory + rules + verification + software, in a portable local package.**

Research by **Mitchell D. McPhetridge** · 11 November 2026

> If memory, rules, verification, and software can travel together, why require a particular notebook, cloud account, or AI provider to reconstruct the system?

This is a offline-first research prototype repository. It contains a full research paper, two deliberately different local browser laboratories, Python and JavaScript verification code, recorded synthetic results, repeatable tests, and a specification for an independent transfer experiment. No remote model, server, account, runtime package download, or internet access is required for the *standalone HTML applications after obtaining the files*.

## Open it in under a minute

1. Unzip the repository and open **`index.html`** in your browser for the editable local page ledger (authoring lab).
2. Open **`web/index.html`** for the stricter **pinned-capsule verifier**. The known demonstration root is prefilled. Ask `kiln-schedule`, `lab-rule`, or `conflicting-answer`.
3. For the offline test, disconnect the network and repeat. Use the built-in export/import actions to demonstrate an explicit data handoff; browser-local storage alone is not transferable across profiles.
4. Read [the core papers](core-papers/README.md): revised manuscript and validation review in PDF, Markdown, and TXT. The original `paper/` paths remain available.
5. Run reproducibility tests with Python 3.8+ and Node.js 18+ if those tools are installed.

### Run the experiment locally

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_browser_core.cjs
node tests/test_authoring_core.cjs
python3 scripts/run_experiment.py
PYTHONPATH=src python3 -m per verify experiment/fixtures/demo_capsule.json --expected-root "$(cat experiment/fixtures/demo_root.sha256)"
PYTHONPATH=src python3 -m per ask experiment/fixtures/demo_capsule.json kiln-schedule --expected-root "$(cat experiment/fixtures/demo_root.sha256)"
```

On Windows, set `PYTHONPATH=src` using your shell syntax or run the Python tests directly. The HTML applications do not require Python or Node; these are optional inspection and rebuilding tools.

To regenerate the browser outputs from the included sources:

```sh
python3 tools/build.py
python3 scripts/build_web.py
```

To rebuild the paper PDF and text versions, see `docs/REPRODUCIBILITY.md`; the finished files are already in the ZIP.

## The two runtime surfaces

| Path | Purpose | Important limitation |
|---|---|---|
| `index.html` | Single-file authoring and exact subject/predicate retrieval; JSON import/export | Self-sealed records are not authenticated; no independent root pinned across the entire editable ledger |
| `web/index.html` | Single-file strict fixed-policy capsule reader and separately expected-root check | Exact-key only; demonstration roots are not digital signatures |
| `src/per/` | Independent standard-library Python capsule verifier and CLI | Requires a locally installed Python runtime; no remote service |

These are **two experiments**, not representations of one interchangeable data format. The authoring ledger uses `PER-LEDGER-1`; the strict capsule uses `portable-evidence-capsule/1`. There is no automatic format-conversion claim.

## What's in the repository

```text
portable-evidence-runtime/
  README.md
  index.html                        Editable offline authoring lab
  core-papers/                      Canonical manuscript and validation review: MD/TXT/PDF
  paper/                            Generated manuscript copies for original links
    Portable_Evidence_Runtime.md
    Portable_Evidence_Runtime.txt
    Portable_Evidence_Runtime.pdf
  web/
    index.html                      Anchored, standalone offline verifier
    source_runtime.js              JavaScript verifier source
  src/
    engine.js                       Authoring-lab engine
    app.js                          Authoring-lab browser interface
    index.template.html
    style.css
    per/                             Python capsule reference engine + CLI
  experiment/
    PROTOCOL.md
    fixtures/                        Synthetic corpus and separately pinned root
    results/synthetic_run.json       15 declared deterministic scenarios
  tests/
    test_reference.py
    test_browser_core.cjs
    test_authoring_core.cjs
  scripts/
    build_web.py
    run_experiment.py
    browser_offline_probe.py
    build_paper.sh
    verify_release.py
  tools/build.py
  docs/
    REPRODUCIBILITY.md
    THREAT_MODEL.md
    DESIGN_BOUNDARIES.md
  GITHUB_CODING_PROMPT.md
```

## Observations and boundaries

- The synthetic scenario runner recorded **15/15 pass**. The Python suite recorded **29/29 pass** (25 original tests, three CLI tests and one 14-case cross-language boundary test) and the strict JavaScript checks **11/11 pass**, authoring checks **10/10 pass**, and offline Chromium checks **13/13 pass** in the preparation environment. The results are reproducible and can change after editing the code.
- SHA-256 checks internal consistency relative to a fixed digest. It is **not a signature, proof of factual accuracy, or proof of authorship**. A self-consistent rehash is rejected by the strict laboratory *only when the expected root is separately retained and trusted*.
- The strict reader answers exact keys, not arbitrary questions. The sample kiln statements are fictional experiment records, not real-world operating instructions.
- Some browsers impose security or file-access restrictions; the optional browser probe records behavior instead of declaring universal compatibility.
- No controlled independent comparison against a hosted workspace or remote model has been run. The paper specifies that study but does not fabricate results.

**Research status:** Public prototype preprint, not peer reviewed or independently validated. See [the publication review](core-papers/Validation_and_Publication_Review.md) for evidence and remaining work. No reuse license has been selected for the code or manuscript.

The automated Chromium trial ran the identical HTML in memory because managed browser policy blocked direct `file://` navigation. Fresh-context export/import passed; physical cross-device and direct-file compatibility remain unverified.

The strict browser requires an expected root to support an answer. The Python and JavaScript APIs and CLI also allow unanchored inspection; omitting `--expected-root` checks internal consistency only. A declared `human` origin is metadata, not authenticated authorship.
