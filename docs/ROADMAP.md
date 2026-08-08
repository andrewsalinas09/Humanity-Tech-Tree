# Roadmap

Phases follow ADR-0014 (tracer bullet first, public UI last). This file always states the **current focus** — update it when the focus changes.

## Current focus
**Phase 0 → Phase 1 transition.** Documentation system established (2026-08-08). Next concrete step: resolve Q-01 (requirement-logic model), then start the Phase 1 tracer bullet.

## Phase 0 — Consolidation ✅ (2026-08-08)
- Mine the old conversations (500KB of chats + README brain-dump) into ADRs, open questions, and architecture docs. Done — see `docs/decisions/` and `docs/archive/digests/`.

## Phase 1 — Golden Spike tracer bullet
Prove the riskiest solver semantics with zero infrastructure:
- C++ console program, hardcoded nodes (suggested slice: Boolean Logic → Vacuum Tubes → Transistor → Intel 4004, plus a Steel/Bessemer bootstrap loop).
- Implement: existence traversal that skips OPTIMIZES edges (ADR-0006), attribute constraints + modifier stack (ADR-0004), state-as-query for at least time (ADR-0002), requirement logic (per Q-01 resolution).
- Output: Graphviz `.dot` dumps — green active paths, red constraint-rejected paths.
- Exit criteria: the vacuum-tube computer path exists but is pruned by a Switching Speed constraint; a bootstrap loop resolves generationally; kill-a-node impact analysis works.

## Phase 2 — Persistence + read-only viewer
- Neo4j schema + serialization (JSON attribute properties), fat-query subgraph fetch (ADR-0010).
- Version-control fields live from the first row (ADR-0011).
- Web read-only viewer (pick stack — Q-12), time slider + region filter driving state-as-query.
- Seed content: hand-authored Golden Spike corridor, a few hundred nodes.

## Phase 3 — Editing + moderation
- Wizard verbs + templates (ADR-0012), search-first creation with aliases.
- ChangeRequest shadow branches, vouching, blast-radius permissions, circuit breakers (ADR-0013).
- Re-parenting check queue with LLM triage (Q-04).

## Phase 4 — Scale
- Ingestion generators (Q-11), embedding services (search, vandalism sentinel, granularity linting).
- LOD architecture (Q-15), transitive-redundancy maintenance (Q-06).
- Community launch: bounty/flag gameplay loops on the home page.
