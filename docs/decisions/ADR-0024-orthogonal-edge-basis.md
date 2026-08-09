# ADR-0024: Edge types are a minimal orthogonal basis — the traversal partition key

- **Status:** Accepted (revised same-day with the user's underlying rationale)
- **Date:** 2026-08-08
- **Source:** user directive + rationale, restart session 2

## Context
The edge enum grew by accretion (~20 types + ~15 floated candidates like FOUNDED, SPUN_OFF_FROM, APPLIES_TO). Unchecked, this ends at a thousand near-synonymous types. But the fix is not maximal collapse either — the real constraint is *why* types exist at all.

## The real rationale (the user's, verbatim in spirit)
At target scale, a traverser must walk a billion-node graph with sub-second selection, and LLM semantic search must find the right relationships without reading everything. **Edge types are the index partition key for traversal**: standing at a high-fan-out node (DuPont with thousands of ingredient AND component edges interleaved), the type is what prunes the fan-out *before* anything else is read. Too many types → overlap, ambiguity, unlearnable for contributors and models. Too few → unselective partitions forcing qualifier scans on every hop. Both directions are failures.

## Decision
1. **The partition test:** a distinction earns an edge TYPE iff a traverser at a high-fan-out node needs it to prune, or a machine consumer (solver, inheritance, counting) treats it differently. It stays a QUALIFIER (slug on the edge instance) if it only matters *after* selection has already narrowed to a small partition.
2. **Rulings the test produces:**
   - Component vs ingredient: **two types** ("contains as part" vs "made from" are different constantly-asked questions across huge interleaved fan-outs — the DuPont case).
   - Type-of vs refinement: **two types** (classification walks vs version walks are different traversals).
   - Spin-off / founded / rebranded / authored / discovered / custody / brand-applies: **qualifiers** — the SUCCEEDS/ASSOCIATION partitions already prune to a handful of edges per node; reading qualifiers there is free. Global qualifier searches are served by a secondary index, not a schema entry.
3. **Straw-man basis (~8, finalized in Q-21 with the user):** ENABLES · IS_COMPONENT_OF · IS_INGREDIENT_OF · IS_TYPE_OF · IS_REFINEMENT_OF · OPTIMIZES · SUCCEEDS · ASSOCIATION.
4. **Qualifier vocabulary grows freely as data** (LLM-canonicalized like attribute names, ADR-0004 pattern) — history's infinite texture at zero schema migrations.
5. **Adding a basis type is a schema event** requiring an ADR that demonstrates a new pruning need or machine behavior. Expected rare.

## Why
Same collapse rule as attributes-not-nodes (ADR-0004), aliases-not-nodes (ADR-0018), name-data-not-nodes (ADR-0022) — applied to edges, with the partition test supplying the principled place to STOP collapsing. The basis is exactly the set of distinctions real traversals prune on; everything else is payload.

## Consequences
- `EdgeType` shrinks to the basis; `DependencyEdge` gains a `qualifier` slug; old→new+qualifier migration table produced in Q-21.
- Qualifiers get a secondary index for global semantic/flavor searches.
- Wizard verbs ask partition-level questions ("does it enable, compose, classify, optimize, succeed, or relate?") and suggest qualifiers.
- TB-038's lineage edges: dated SUCCEEDS(qualifier: spun-off) and ASSOCIATION(qualifier: founded / produced-by).
