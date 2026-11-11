# Design boundaries

## What is concretely inside this archive

- Two browser-readable, offline capable HTML files; one is an editable sealed-page workspace, the other is a fixed-policy capsule verifier.
- JavaScript source for both modes, Python standard-library verification for the capsule mode, deterministic fixtures, and repeatable tests.
- A 15-case synthetic result file, expected root, source JSON, full paper and proposed controlled trial.

## What is intentionally outside the bounded implementation

- General-purpose LLM inference or meaning extraction.
- Truth detection, signer identification, trusted publication timestamps, or public-key infrastructure.
- Formal multi-writer merging, distributed consensus, remote access control, per-user secrets, and secure synchronization.
- Production multi-tenant service, isolation/sandboxing against arbitrary uploaded code, or automated data permission review.
- General equivalence of the authoring ledger and strict capsule format.

The goal is *minimal transfer closure for declared operations*. It does not imply that a portable file contains a full AI system, only that the declared verifiable operation can run without relying on an external service.
