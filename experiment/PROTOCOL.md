# PER-001: Portable evidence recovery and refusal experiment

**Investigator:** Mitchell D. McPhetridge\
**Version:** 0.1 · 11 November 2026\
**Stage:** Synthetic engineering evaluation completed; independent comparative trial proposed.

## Question

Can a copyable unit containing the evidence, rules, verifier, and reader reproduce the same allowed answers and refusals when the network, source account, notebook, and remote AI provider are unavailable?

## Scope and operational claim

A *portable success* is a correct answer or correct refusal from a locally obtained capsule under its declared exact-key grammar with no remote call. Hash verification must reject changed bytes relative to a retained anchor, and an unknown, conflicting, blocked, retired, or machine-origin-only answer must not be promoted.

A result is **not** evidence that the sample source statements are true or that unrestricted questions are understood.

## Fixed synthetic data

`fixtures/demo_source.json` contains fixed candidate records; `fixtures/demo_capsule.json` is the canonical wrapper; `fixtures/demo_root.sha256` is the independently recorded expected root. Do not rewrite these files during a reproduction. Changes create a different experiment and must receive a new ID and recorded hash.

Test cases (exact predicted states):

| Case | Expected outcome |
|---|---|
| valid_pinned | verification succeeds |
| exact_source | supported |
| retired_excluded | supported newer source, revision 2 |
| machine_excluded | not_in_corpus |
| blocked_excluded | not_in_corpus |
| ambiguous_refused | ambiguous |
| unknown_refused | not_in_corpus |
| paraphrase_refused | invalid_key |
| value_corruption_refused | integrity_error |
| status_corruption_refused | integrity_error |
| policy_corruption_refused | integrity_error |
| root_corruption_refused | integrity_error |
| relocated_capsule | supported after copy |
| rehashed_substitution_pin_refused | integrity_error |
| missing_all_bytes_refused | integrity_error |

Execute `python3 scripts/run_experiment.py`, inspect every `pass` value in `results/synthetic_run.json`, and rerun the Python and JS unit tests. The runner records actual statuses; do not edit failed entries into success.

## Browser trial

1. Copy only `web/index.html` to a local folder.
2. Disable networking and use a fresh browser profile, if practical.
3. Open that file as `file://`, verify the pinned synthetic capsule, ask `kiln-schedule`, then `conflicting-answer`.
4. Alter the expected-root input to all zeros; a supported answer must stop.
5. Restore the original root and verify the valid answer returns.
6. Export the capsule, open a new profile, and import it. The independently retained root is required again.
7. Run the optional `scripts/browser_offline_probe.py` with installed Playwright/Chromium; save its JSON output and capture browser/version/errors. The standalone HTML itself has no Python dependency.

Record: browser/version, OS, transfer medium, network blocked/not, whether script executed, root match, each answer status, whether any network requests occurred, bytes transferred, human interventions, and cold-start elapsed time.

## Proposed comparison (NOT YET EXECUTED)

C0 pointer-only service handoff; C1 exported local notes without executable policy; C2 portable self-consistent capsule without a trusted independent root; C3 portable capsule with independently supplied expected root. Use matched sources, tasks, participants, and fresh sessions. Report precision and coverage separately. Predeclare which negative conditions count as legitimate refusal.

Primary measures: wrong supported answers, legitimate supports, correct refusals, false refusals, wrong-authority promotions, offline transfer success, dependency count. Secondary: time, interventions, bytes and equipment needs. Do not compare a content fetch latency directly with a metadata search latency or imply a controlled speedup from unmatched workloads.

## Criteria to reject the claim

A required undocumented online request, unsupported valid transfer on a claimed supported browser, support from changed data with unchanged independent root, wrong promotion of an ineligible record, or unexplained divergence between local implementations is a recorded failure. Do not suppress failures from final reports.
