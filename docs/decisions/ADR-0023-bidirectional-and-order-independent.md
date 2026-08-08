# ADR-0023: Navigable both ways; convergent under any authoring order

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user, restart session 2 ("Nokia to paper mill and paper mill to phone and anywhere in between — they can add it anywhere and not be wrong")

## Context
Contributors will start rabbit holes anywhere in a chain — the org, the product, the ancestor — and build outward in any direction. The architecture must guarantee neither browsing nor authoring privileges any direction or order.

## Decision
1. **Direction is meaning, not access.** Edges keep exactly one semantic direction (provider → consumer), but every edge is indexed and navigable both ways in every store and viewer (reverse adjacency in the solver; native in Neo4j). "Show me everything this led to" and "show me everything this needed" are equal first-class queries.
2. **Insertion-order independence is an invariant.** Any sequence of true additions converges to the same effective graph regardless of order. Every authoring verb must be valid against any existing fragment: parents-first, children-first, middle-out. This already follows from the existing non-destructive machinery — stubs (unknown references), lazy abstraction (late parents), additive specialization (late detail), lifting, exclusions — and this ADR pins it as a promise no future mechanism may break.
3. **Merge is the healing half of convergence.** Independent starts meeting in the middle under different names (Nokia's rubber era as "Finnish Rubber Works" vs "Suomen Gummitehdas") produce duplicates — incomplete, not wrong (ADR-0015) — healed by search-first authoring (Q-20) and MIGRATED_TO redirects (ADR-0011). Convergence is defined up to merges.
4. **Executable test:** permute the insertion order of a fixed fact set; assert the effective graphs (post-merge) are identical. This becomes a standing fixture in the eventual test suite, run against every new mechanism.

## Why
"Add it anywhere and not be wrong" is the property that makes crowdsourced rabbit-hole authoring viable at all — nobody has a map of the whole chain, so the graph must be assembled from fragments in arbitrary order. Making it an explicit invariant (rather than a lucky consequence) means every future design change gets checked against it, like the prime directive.

## Consequences
- Any proposed mechanism whose result depends on edit order is rejected or must be reworked (this is now a TESTBED-level acceptance criterion).
- Viewer requirement: symmetric up/down navigation from any node.
- TB-037 → Solved (design).
