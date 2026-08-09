# Stress test 2026-08-08 — full adversarial record

This folder preserves the COMPLETE red-team record for future agents: every surviving finding's full scenario, claimed failure, and the skeptic verifier's complete adjudication. Summary + reading of results: `../2026-08-stress-test-report.md`. Hardening rules produced: **ADR-0035 (H1-H17)**; test cases **TB-047..TB-063**.

## Methodology
17-agent workflow: 7 finders (one per attack dimension below, each REQUIRED to find different things — TESTBED-covered ground disallowed) → dedup agent (28 raw → 26 distinct) → 9 skeptic verifiers defending the architecture, walking each scenario through the documented mechanisms. Verdicts: BREAKS (verified real gap) / PARTIAL (small named missing rule) / HANDLED (refuted — existing machinery covers it).

## Result: 0 BREAKS · 17 PARTIAL · 9 HANDLED

| Finding | Dimension | Severity | Verdict |
|---|---|---|---|
| F 1 | Temporal edge cases | high | **PARTIAL** |
| F 3 | Temporal edge cases | medium | **PARTIAL** |
| F 4 | Temporal edge cases | medium | **PARTIAL** |
| F 2 | Temporal edge cases | high | **HANDLED** |
| F 5 | Mutation & refactor storms | high | **PARTIAL** |
| F 6 | Mutation & refactor storms | high | **PARTIAL** |
| F 7 | Mutation & refactor storms | high | **PARTIAL** |
| F 8 | Mutation & refactor storms | medium | **PARTIAL** |
| F 9 | Errors & recovery | high | **PARTIAL** |
| F 11 | Errors & recovery | medium | **PARTIAL** |
| F 10 | Errors & recovery | high | **HANDLED** |
| F 12 | Solver semantics adversarial | high | **PARTIAL** |
| F 13 | Solver semantics adversarial | high | **PARTIAL** |
| F 14 | Solver semantics adversarial | high | **PARTIAL** |
| F 15 | Solver semantics adversarial | medium | **HANDLED** |
| F 17 | Concurrency & commutativity | high | **PARTIAL** |
| F 16 | Concurrency & commutativity | high | **HANDLED** |
| F 18 | Concurrency & commutativity | medium | **HANDLED** |
| F 19 | Trust-system gaming | high | **PARTIAL** |
| F 20 | Trust-system gaming | high | **PARTIAL** |
| F 21 | Trust-system gaming | high | **PARTIAL** |
| F 22 | Trust-system gaming | medium | **HANDLED** |
| F 24 | Identity & abstraction paradoxes | high | **PARTIAL** |
| F 23 | Identity & abstraction paradoxes | high | **HANDLED** |
| F 25 | Identity & abstraction paradoxes | medium | **HANDLED** |
| F 26 | Identity & abstraction paradoxes | medium | **HANDLED** |

## Files
- `findings/01-temporal.md` — Temporal edge cases (4 findings)
- `findings/02-mutation.md` — Mutation & refactor storms (4 findings)
- `findings/03-errors.md` — Errors & recovery (3 findings)
- `findings/04-solver.md` — Solver semantics adversarial (4 findings)
- `findings/05-concurrency.md` — Concurrency & commutativity (3 findings)
- `findings/06-trust.md` — Trust-system gaming (4 findings)
- `findings/07-identity.md` — Identity & abstraction paradoxes (4 findings)

## For future agents
When re-stress-testing: read this folder first so you attack NEW ground; the HANDLED entries double as worked proofs of mechanism composition; the PARTIAL entries show the historical seams — check their H-rules (ADR-0035) are still honored by any design change you propose.
