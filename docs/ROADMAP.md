# Roadmap

Phases follow ADR-0016 (tree first; solver is Phase 4). This file always states the **current focus** — update it when the focus changes.

## Current focus
**Phase 1 — schema lock via the test bed.** Work through `docs/TESTBED.md`: drive every OPEN/Partial case to Solved (design). Q-01 resolved (ADR-0017 expression trees); Q-18 resolved (ADR-0018 version families, worked 802.11 example). Next up: Q-02 (truth-system overlap), then the EdgeType enum reconciliation and remaining Partial cases (TB-011, TB-029, TB-031). Design changes happen HERE, on paper, where they're still cheap — that's the whole point of this phase.

## Phase 0 — Consolidation ✅ (2026-08-08)
Doc system built; 10k lines of old chats distilled into ADRs, open questions, digests. Test bed established (2026-08-09).

## Phase 1 — Schema lock + test bed
- Every TESTBED case Solved (design) or explicitly accepted-open (like Q-10 quantities).
- Resolve at minimum: Q-01 (logic model), Q-02 (truth-system overlap), Q-18 (version families), Q-19 (high-fan-in authoring).
- Every mechanism passes the ADR-0015 litmus test: failure modes produce incompleteness, never wrongness.
- Output: a frozen v1 schema document (prose + serialization format), designed for changeability.

## Phase 2 — The tree itself
- Hand-author a seed corridor (e.g. iPhone → modem/WiFi → 802.11 family → TSF; battery branch; CPU branch) in a simple migration-friendly format (plain files/SQLite — NOT the at-scale engine, see Q-17).
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
