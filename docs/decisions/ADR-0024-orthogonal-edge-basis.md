# ADR-0024: Edge types are a minimal orthogonal basis; flavor is a qualifier, never a type

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user directive, restart session 2 ("spun off from is just a child... each edge MUST be orthogonal to every other edge, no questions")

## Context
The edge enum grew by accretion (~20 types plus ~15 pending candidates like FOUNDED, SPUN_OFF_FROM, APPLIES_TO, PRODUCED_BY). Left unchecked this ends at a thousand near-synonymous types for every way something can relate to something — unlearnable for contributors, unmaintainable at billions of edges, and full of overlap that makes queries ambiguous.

## Decision
1. **The orthogonality test:** two edge types may both exist only if some machine consumer (solver, traversal, inheritance, counting, rendering layer) must treat them differently. If only the human meaning differs, it is ONE type plus a **qualifier** (a slug/attribute on the edge instance).
2. **Flavor is data.** "Spun off," "founded," "licensed," "rebranded," "authored," "discovered," custody periods — qualifiers on basis edges, never new types. The qualifier vocabulary grows freely without schema migrations; qualifier hygiene is handled like attribute names (LLM canonicalization, ADR-0004 pattern).
3. **Q-21 becomes a reduction pass, not a collection pass:** map every existing and pending type onto a minimal basis. Straw-man basis (~6, to be finalized WITH the user — the judgment calls are theirs): ENABLES (existence traversal), PART_OF (composition/counting), SUBTYPE (taxonomy/inheritance), OPTIMIZES (skipped by existence, read by cost), SUCCEEDS (dated succession story), ASSOCIATION (ghost layer, solver-invisible).
4. **All candidate types previously floated in ADRs/examples (APPLIES_TO, FOUNDED, SPUN_OFF_FROM, PRODUCED_BY, DISCOVERED_USING, etc.) are hereby qualifiers pending the Q-21 reduction** — this supersedes any earlier note implying they'd become enum members.
5. Adding a genuinely new basis type is a schema event requiring an ADR demonstrating a new machine behavior — expected to be rare-to-never.

## Why
This is the same collapse rule used everywhere else in the design — purity is an attribute not a node (ADR-0004), WiFi 6 is an alias not a node (ADR-0018), rebrands are name data not new nodes (ADR-0022) — finally applied to edges, the last place accretion was still legal. A closed basis keeps contributors' mental model learnable (six questions: does it enable, compose, classify, optimize, succeed, or just relate?), keeps queries unambiguous, and makes history's infinite texture expressible at zero marginal schema cost.

## Consequences
- `EdgeType` enum will shrink, not grow; `DependencyEdge` gains a `qualifier` slug. Executed in the Q-21 pass (with data-migration mapping table old→new+qualifier).
- Wizard verbs ask basis-level questions and offer qualifier suggestions.
- TB-038's "vocabulary gap" dissolves: FOUNDED/SPUN_OFF_FROM/custody are qualifiers on ASSOCIATION/SUCCEEDS edges.
