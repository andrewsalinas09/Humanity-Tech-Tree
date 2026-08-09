# ADR-0016: Tree-first build order — the graph is the product; the solver is a later feature

- **Status:** Accepted (supersedes ADR-0014)
- **Date:** 2026-08-08
- **Source:** user, restart session 2

## Context
ADR-0014 put a C++ constraint solver first ("tracer bullet"). The user's correction: the solver was always an *added* feature. The tree in isolation — browsable dependencies with honest metadata — is already the core value ("a database you can get lost in for hours"), and the community correctness layer (LLM triage + human voting) is more critical to the mission than simulation, because the project lives or dies on being citable and reliable.

## Decision
Build order:
1. **Schema lock + test bed** — validate the data model on paper against every TESTBED case; resolve blocking questions (Q-01 first).
2. **The tree itself** — hand-authored seed corridor in a simple, migration-friendly format; a browsable read-only rabbit-hole viewer.
3. **Community correctness layer** — editing verbs, shadow branches, LLM triage + voting, provenance/citations (ADR-0012/0013). This is core product, not an add-on.
4. **Solver/simulation** — constraint pruning, state-as-query computation, impact analysis (ADR-0002/0003/0004/0006 semantics).
5. **Scale** — ingestion, LOD, storage hardening.

Constraint, optimization, and versioning *data* is still captured on nodes/edges from day one (per ADR-0011's "schema now, features later" logic) so the solver bolts on later without migration.

## Why
Value ordering: a correct browsable tree serves every use case the user cares about before any simulation runs; moderation is what makes it correct. Risk ordering: the irreversible thing is the *data model at scale*, not the solver — so paper-validate the schema hard (test bed), keep early storage trivially migratable, and defer engine commitments (see Q-17). The solver loses nothing by waiting: its semantics are already specified in ADRs and exercised by TESTBED cases.

## Consequences
- ADR-0014 is superseded; its Golden-Spike/God-Mode ideas survive inside Phase 4.
- Until the solver exists, constraint pruning doesn't run — technically-true-but-absurd paths are visible in the raw tree. Acceptable under ADR-0015 (they're true), mitigated in the viewer by epistemic/zoom filtering.
- Phase 2 storage must be chosen for *changeability*, not performance (plain files/SQLite fine); the at-scale engine decision is deliberately reopened (Q-17).
