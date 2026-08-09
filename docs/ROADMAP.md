# Roadmap

Phases follow ADR-0016 (tree first; solver is Phase 4). This file always states the **current focus** — update it when the focus changes.

## Current focus
**Phase 1 reviewed and revised.** External pre-build review adopted (2026-08-08): ADR-0037 (three-valued entailment — UNKNOWN is first-class), ADR-0038 (assertions first-class + identity/assertion reference invariant, the fourth constitutional screen), document authority hierarchy established (SCHEMA/ADRs/TESTBED normative; ARCHITECTURE/README derived). **Phase 2 order:** (0) reference semantics kernel + ~20 TESTBED cases as executable tests → (1) Postgres schema + fact log → (2) MCP server → (3) existence gate → (4) read-only viewer → (5) the iPhone-all-the-way-up seed corridor, where reality attacks the ontology.

## Phase 0 — Consolidation ✅ (2026-08-08)
Doc system built; 10k lines of old chats distilled into ADRs, open questions, digests. Test bed established (2026-08-08).

## Phase 1 — Schema lock + test bed
- Every TESTBED case Solved (design) or explicitly accepted-open (like Q-10 quantities).
- Resolve at minimum: Q-01 (logic model), Q-02 (truth-system overlap), Q-18 (version families), Q-19 (high-fan-in authoring).
- Every mechanism passes the ADR-0015 litmus test: failure modes produce incompleteness, never wrongness.
- Output: a frozen v1 schema document (prose + serialization format), designed for changeability.

## Phase 2 — The tree itself
- Seed corridor (user ruling): **the iPhone, all the way up** — one thread pulled honestly, following wherever it leads (TSMC, CPUs, operating systems, WiFi → encryption → the math, batteries, materials). It organically hits the Microprocessor density test (TB-013) and math conditionality without staging them. Built directly on **Postgres** (ADR-0031, ratified) — starts tiny, no interim format, JSONL fact-log export from day one.
- Read-only rabbit-hole viewer: click any node, see parents/children, time + region + epistemic filters. This is the first moment the project is *usable and lovable*.
- Authoring done via scripts/agent sessions applying the wizard-verb semantics (ADR-0012) even before UI exists.

## Phase 3 — Community correctness layer (core product)
- Editing verbs + templates, search-first creation with aliases.
- ChangeRequest shadow branches, vouching, blast-radius permissions, circuit breakers (ADR-0013).
- LLM triage + human voting pipelines (Q-04): re-parenting queues, flag/bounty review.
- Citations/provenance surfaced everywhere — this is what makes the tree citable.

## Phase 4 — Solver & simulation
- Constraint pruning, modifier stacks, state-as-query, optimization paths, impact analysis (ADR-0002/0003/0004/0006).
- The old ADR-0014 "God Mode"/Golden Spike ideas live here.

## Phase 5 — Scale
- Storage engine decision at real data volumes (Q-17; ~TB-scale estimate), ingestion generators (Q-11), embedding services, LOD (Q-15), transitive-redundancy maintenance (Q-06).
- Community launch: bounty/flag gameplay on the home page.
