# ADR-0028: The final edge basis — 8 types — and the legacy migration table

- **Status:** Accepted (closes Q-21)
- **Date:** 2026-08-08
- **Source:** user rulings across restart session 2; partition test per ADR-0024

## Context
Q-21 required reducing ~20 enum members + ~15 floated candidates to the orthogonal basis. All rulings are in: component≠ingredient and type-of≠refinement stay (DuPont selectivity); KNOWLEDGE_REQUIREMENT and SPECIFIES_STANDARD collapse into ENABLES (ADR-0025 masks + target-category pruning); story flavors are qualifiers. The last call — one story partition or two — is settled by the user's deeper principle: **this is a tech tree first and foremost; events, people, and orgs are supporting cast, present only where they shape technology.** Building two partitions for second-class content now would violate lazy abstraction. Because flavor lives in qualifiers, a future split is a mechanical migration (`type = f(qualifier)`, zero information loss), so deferring costs nothing.

## Decision
**The basis (8):**

| Type | Machine semantics |
|---|---|
| ENABLES | existence dependency; possibility traversal (with ADR-0025 masks) |
| IS_COMPONENT_OF | assembled part; BOM counting |
| IS_INGREDIENT_OF | consumed/transformed input |
| IS_TYPE_OF | classification; inheritance flows down (ADR-0019) |
| IS_REFINEMENT_OF | version/generation walks; flat stars (ADR-0018) |
| OPTIMIZES | attribute improvement; existence dead-end (ADR-0006) |
| SUCCEEDS | dated succession; timeline-wave rendering; REPLACED-implies-usage-shift |
| ASSOCIATION | story/attribution ghost layer; solver-invisible |

**Legacy migration table (old → new + qualifier):**

| Legacy | Becomes |
|---|---|
| DEPENDENT_FOR | ENABLES |
| SPECIFIES_STANDARD | ENABLES (target category STANDARD_UNIT prunes) |
| KNOWLEDGE_REQUIREMENT | ENABLES (+ BIOLOGICAL_ENTITY linter rule; ADR-0025 mask) |
| IS_COMPONENT_OF / CONTAINS | IS_COMPONENT_OF |
| IS_INGREDIENT_OF | IS_INGREDIENT_OF |
| IS_TYPE_OF | IS_TYPE_OF |
| IS_REFINEMENT_OF | IS_REFINEMENT_OF |
| OPTIMIZES / SIGNIFICANTLY_IMPROVES | OPTIMIZES (degree lives in OptimizationFactors) |
| REPLACED_BY | SUCCEEDS(replaced) |
| SUPERSEDED_BY | SUCCEEDS(superseded) |
| SPUN_OFF_FROM (floated) | SUCCEEDS(spun-off) |
| rebrand/fork/merge flavors | SUCCEEDS(rebranded / forked / merged) |
| AUTHORED | ASSOCIATION(authored) |
| DISCOVERED | ASSOCIATION(discovered) |
| INVENTED | ASSOCIATION(invented) |
| INFLUENCED | ASSOCIATION(influenced) |
| PLACE_OF_STUDY_FOR | ASSOCIATION(studied-at) |
| DISPROVED_BY | ASSOCIATION(disproved) |
| INHIBITS / STIFLES | ASSOCIATION(suppresses) |
| MOTIVATED_BY | ASSOCIATION(motivated) |
| DRIVES_NEED_FOR / ACCELERATES_DEMAND | ASSOCIATION(drives-need / accelerates-demand) |
| PRECIPITATED | ASSOCIATION(precipitated) |
| GAVE_RISE_TO | ASSOCIATION(gave-rise-to) |
| PROVIDES_RESOURCES | ASSOCIATION(provides-resources) |
| EXPLAINS_PRINCIPLE / CODIFIES / DESCRIBES_METHOD | ASSOCIATION(explains / codifies / describes-method) |
| FUNDED | ASSOCIATION(funded) |
| ADOPTS | ASSOCIATION(adopted) |
| DISCOVERED_USING | ASSOCIATION(discovered-using) |
| FOUNDED (floated) | ASSOCIATION(founded) |
| APPLIES_TO brand (floated) | ASSOCIATION(brand-applies) |
| PRODUCED_BY custody (floated) | ASSOCIATION(custody) |
| MIGRATED_TO | not an edge — node-level merge-redirect fact (ADR-0011) |

## Why
Eight partitions is exactly the set real traversals prune on; everything else is payload. The one-story-partition call applies the user's tech-first principle plus lazy abstraction to the schema itself, with a costless escape hatch.

## Consequences
- `Node.cpp`: EdgeType enum rewritten to the basis; `qualifier` field added to DependencyEdge.
- Q-21 → Resolved. Remaining Q-21 deliverables that carry forward as Phase 1 tasks: per-type category-compatibility rules (linter) and the starter qualifier vocabulary (LLM-canonicalized, ADR-0004 pattern).
- If story traversal profiling ever demands it, split ASSOCIATION mechanically by qualifier — requires only a migration note, not a redesign.
