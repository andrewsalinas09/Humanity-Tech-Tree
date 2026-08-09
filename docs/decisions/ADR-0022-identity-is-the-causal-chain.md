# ADR-0022: Identity is the causal chain; names and brands are data, promotable to nodes

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user exercise (product morphing / Ship of Theseus, TB-036); worked example `docs/examples/product-morphing-worked-example.md`

## Context
Products mutate: rebrands with continuous history, gradual total replacement (Ship of Theseus), brand transplants onto mechanically unrelated successors (Mustang → Mach-E), zombie brands (Polaroid), forks, pivots. The trap is storing a "sameness" judgment the graph must then defend forever.

## Decision
1. **No sameness property exists.** Identity is displayed, never asserted: dated nodes, dated edges, succession chains. "Is it the same thing?" is a question the graph renders the evidence for and refuses to answer.
2. **Names are dated data:** nodes gain a lazy `name_history` (dated names); `aliases` remain undated search keys. Rebrands are data changes recorded by versioning (ADR-0011), not node surgery.
3. **Brands promote to nodes lazily, only on transplant.** While a brand tracks its original bearer it is mere name data. The moment it detaches (applied to a mechanically unrelated product line, licensed, outliving its org), promote it to a Brand node with dated `APPLIES_TO` edges to each bearer — the lift pattern (ADR-0018) applied to identity. Mechanical descent (`IS_REFINEMENT_OF`) must never be asserted just because a brand moved; marketing lineage is a narrative edge (GAVE_RISE_TO).
4. **Family roots degrade gracefully.** As generations churn, family-wide claims get date-bounded, widened, or pushed down to generation nodes; a root reduced to name + succession + story edges is a legal, honest end state — an identity container.

## Why
Every mutation in the taxonomy (rebrand, Theseus, transplant, zombie brand, pivot, fork, merge, category drift) resolves into existing machinery — ADR-0011/0015/0018 — plus dated names and the brand-promotion pattern. Refusing the sameness question is what makes this robust: any stored "same/different" flag would eventually be wrong (ADR-0015), whereas chains of dated facts cannot be.

## Consequences
- `Node.cpp`: `DatedName {name, start?, end?}` + `name_history` on nodes; Brand nodes + `APPLIES_TO` edge type join the vocabulary (edge-enum reconciliation pass will formalize).
- Search must index `name_history` alongside `aliases` (Q-20 pipeline).
- TB-036 → Solved (design).
