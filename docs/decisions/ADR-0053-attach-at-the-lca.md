# ADR-0053: Attach at the earliest common ancestor (the LCA rule)

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user ruling ("we need to always hook up to the earliest common ancestor — not iPhone / Samsung but Smartphone (charging)")

## Context
Wiring a dependency to every instance separately (charging → iPhone, charging → Galaxy, charging → Pixel…) multiplies edges, invites drift, and makes ubiquitous-dependency wiring (Q-28) quadratic. ADR-0005 settled *which edge* carries a requirement (the consumer's); ADR-0019 settled how families *distribute* edges (inheritable defaults + presumptions); this settles *which node* an edge should attach to.

## Decision
1. **A claim attaches at the earliest (highest) common ancestor for which it is true.** Charging attaches to Smartphone, not to each phone; instances inherit it as presumptions (ADR-0019); genuinely instance-specific truths still attach at instances; exceptions use EXCLUDE/WIDEN.
2. **Attaching low remains LEGAL** — technically-correct-accepted is not negotiable (ADR-0015); the low edge is true, merely mis-altitude. The heal is the existing hoist machinery: `extract_family` on the existing family (it works incrementally — classify edges are skipped when present, shared claims hoist, instance edges shadow as covered history).
3. **The hoist linter** watches for the violation: a family whose children (≥2) share an unshadowed claim the family lacks gets a WANT_COVERAGE bounty ("hoist shared claims to X") naming the hoistable claims. Deduped against open AND fulfilled requests, so a deliberate keep-per-instance choice (the Galaxy glass case) is nagged at most once — close the bounty with a note and it stays closed.
4. Q-28 corollary: ubiquitous-dependency campaigns wire families first by construction — the LCA rule is what makes "add electricity to everything" mean dozens of edges, not thousands.

## Consequences
- run_hoist_linter joins the linter squad (sibling clusters, texture) on tile-state rebuild.
- Future authoring nudge (unbuilt): add_* verbs could offer "this claim may belong on the family FAMILY — attach there?" when the consumer has siblings; deferred to avoid gate noise — the linter heals post-hoc, which matches the emergent-grouping philosophy (Q-26).
