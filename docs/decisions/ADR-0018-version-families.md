# ADR-0018: Version families — flat significance-gated stars with truth-granular feature attachment

- **Status:** Accepted (resolves Q-18)
- **Date:** 2026-08-08
- **Source:** worked example `docs/examples/802-11-worked-example.md` (validated against 802.11, Thunderbolt, DDR, and the CPU fan-out case)

## Context
Versioned families (802.11 b/g/n/ax, Thunderbolt 3/4/5, DDR) and high-fan-out concepts (one CPU node, hundreds of divergent consumers) threatened either node explosion or an un-navigable mush — including the "graph inside a node" temptation of storing a nested sub-graph.

## Decision
1. **Family root node** carries everything true family-wide: shared dependencies, family-wide mechanisms (TSF → 802.11 root), iteration records for non-significant versions, and marketing aliases (WiFi 6).
2. **Version nodes exist only where the Significance Filter (ADR-0009) passes** — for standards, effectively "introduced a genuinely new dependency" (n ← MIMO, ax ← OFDMA). Certification/regulatory tweaks (802.11j, Thunderbolt 4) are iteration records.
3. **Flat star, not a chain:** every version node is `IS_REFINEMENT_OF → family root`. Version-to-version succession is story, expressed with dated REPLACED_BY/SUPERSEDED_BY edges that requirement inheritance ignores.
4. **Features attach at the granularity where they are true:** family-wide → root; version-specific → edges to exactly the versions that have them (non-contiguous presence is naturally supported — solves TB-006/TB-033); versions without nodes → iteration-record data, **lifted** into edges if the version later earns a node. Lifting is a monotone resolution increase (ADR-0015).
5. **Consumers:** historical instances link to the version they actually used (most specific truth, ADR-0008); abstract consumers link to the root, optionally with edge constraints. Creating a new version node migrates nothing by default — the check queue only *suggests* repointing where the new version is a consumer's more specific truth.
6. **No nested sub-graphs in storage.** The "inner world" of a family is ordinary scoped nodes/edges; collapsing them into the family bubble is zoom/LOD *rendering* (Q-15), not schema.
7. **High-fan-out concepts are the dual case:** one role node, architecture divergence as refinement children, diversity carried on consumer edges' constraints, recurring demand profiles bundled by capability router nodes. Growth is linear in consumers plus sublinear routers.

## Why
The worked example reproduced real 802.11 history — including legislation dependencies, cross-domain bridges, and the org-vs-brand split — with zero new machinery: every rule is an application of ADR-0003/0008/0009/0015. Flat stars keep inheritance clean (chaining would drag version-specific baggage down the chain). Misjudging node-worthiness is recoverable in both directions (create-later + lift, or merge + redirect), so the filter's editorial judgment calls carry no structural risk.

## Consequences
- TB-013, TB-014, TB-015, TB-033 → Solved (design); TB-006's queryability gap closes via truth-granular attachment.
- The Phase 2 seed corridor must include the Microprocessor node at real consumer density as the empirical stress test.
- Iteration records need a defined lifting operation (record → node + edges) in the eventual edit verbs.
