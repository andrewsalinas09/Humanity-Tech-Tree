# ADR-0021: Redundant truth is shadowed, never removed

- **Status:** Accepted (resolves Q-06)
- **Date:** 2026-08-09
- **Source:** user question "do we break iPhone → camera?", restart session 2; motivating cases TB-025, TB-035

## Context
Three recurring shapes produce edges that are still true but covered by higher-resolution edges: transitive zoom-outs (iPhone→Lithium once iPhone→Battery→Lithium exists), additive specialization (generic camera + front + rear, guaranteed routine by ADR-0020), and refinement chains. Counting/BOM queries must not double-count; deleting the coarse edge is forbidden (ADR-0011) and wrong (the edge is true — ADR-0015). Q-06 had three candidate mechanisms and no decision.

## Decision
1. **Shadowing is the mechanism.** An edge may carry a subsumption record: `shadowed_by: [edge_ids]` — the set of finer edges that fully cover its claim. The edge itself is never modified, moved, or deleted.
2. **Set at edit time, suggested by a linter, confirmed by humans.** The Specialize/Intercept verbs ask "is the original edge now fully covered?" and write the record. A background redundancy linter (graph reachability + semantics) *proposes* shadow marks through the normal review lane; nothing is ever auto-shadowed destructively, and the periodic "transitive reduction" job from the old design becomes this linter — it proposes, never deletes.
3. **Query semantics:** counting/BOM/traversal-for-composition skip shadowed edges; existence/truth queries treat them as valid (they are true); zoomed-out rendering may prefer them (one "camera" edge at low zoom instead of three).
4. **Shadows re-validate when covering edges change.** If a covering edge is date-bounded, excluded, or itself shadowed such that coverage no longer holds, the shadowed edge automatically resurfaces as the truth carrier. The record is derived metadata over immutable truth — visibility flexes, truth is monotone.
5. **PRIMARY_REFINEMENT proxy redirects remain a separate tool** for "consumers should *move*" situations (re-parenting suggestions, Q-04 lane) — that is migration advice, not redundancy masking; the two must not be conflated.

## Why
Shadowing is the only candidate that satisfies all constraints at once: no deletion (ADR-0011), no false claims (ADR-0015 — the coarse edge stays true), correct counts, cheap zoomed-out answers, full reversibility, and locality (a shadow check touches only the edge's neighborhood, which matters at billions of edges). Break-and-replace fails on history, provenance references, and churn; pure batch transitive reduction fails on ADR-0011 and on semantics (some "redundant" edges carry independent claims — hence human confirmation).

## Consequences
- `DependencyEdge` gains `shadowed_by_edge_ids` (empty = live).
- Every query type must declare whether it reads shadowed edges (counting: no; truth: yes; rendering: zoom-dependent).
- The linter needs a definition of "fully covers" per edge type — deferred to solver-phase specification; edit-time human judgment suffices for Phase 2.
- Q-06 → Resolved. TB-025, and TB-035's caveat → Solved.
