# ADR-0017: Requirement logic is a boolean expression tree on the consumer node

- **Status:** Accepted (resolves Q-01; replaces both prior designs)
- **Date:** 2026-08-08
- **Source:** user + assistant, restart session 2

## Context
Two competing designs coexisted (Q-01, TB-021): Node.cpp's three-level `LogicGroup` (slot AND → variant OR → part AND, flattened into integer IDs on edges) and the abstraction chat's single-level `alternative_path_id`. Neither expresses arbitrary nesting ("one expert OR a team of ten, where the team is itself a bundle"), and integer-ID encodings were repeatedly found confusing.

## Decision
Each node MAY carry one boolean expression tree over its incoming dependency edges:
- **Leaves** reference edge IDs; **internal nodes** are AND / OR / NOT, arbitrarily nested.
- **Absent expression = AND of all hard dependency edges** (the default). Edges not referenced by an existing expression are implicitly ANDed in.
- **NOT is legal but editorially discouraged**: the rest of the design is monotone (adding information only unlocks), which is what makes graceful ignorance (stub nodes, incomplete graphs) safe. NOT breaks monotonicity — adding a node can flip a requirement to unsatisfied — so it exists for completeness and waits for a real case.
- Serialization is a small recursive JSON object, e.g. `{"or": ["edge_platinum", {"and": ["edge_palladium", "edge_heat"]}]}`.
- Visual grouping stays separate (`visual_category_slug` on edges), per the earlier logic-vs-visuals separation.

`LogicGroup` and `alternative_path_id` are both retired; edges carry no logic integers.

## Why
- AND/OR/NOT over edge leaves is functionally complete — it covers every case either old design could express, plus the nesting the user originally asked for (TB-021: `OR(platinum, AND(palladium, heat))`; `OR(expert, AND(p1…p10))`).
- Putting the tree on the consumer node matches ADR-0005 (requirements belong to the consumer) and keeps edges simple.
- The absent-expression default keeps lazy authoring legal and makes the common case (all components required) zero-cost. When a contributor adds a second edge filling the same role, the Componentize wizard (ADR-0012) asks "alternative or additional?" — mis-authored logic is ordinary editable content fixed by moderation, while the schema itself can always express the truth (ADR-0015).
- Trees serialize/version cleanly (ADR-0011) and evaluate trivially in the eventual solver.
- K-of-N ("any 2 of 4") is expressible today (expanded OR-of-ANDs) and can be added later as syntactic sugar without breaking anything — consistent with "design it so it's easy to change."

## Consequences
- `Node.cpp`: `LogicGroup` struct and `DependencyEdge::requirement_logic` removed; `HistoryNode` gains an optional `RequirementExpr` tree.
- TB-021 → Solved (design). Q-01 → Resolved.
- Solver (Phase 4) evaluates the tree with tri-state logic in mind (unknown edges under graceful ignorance); NOT-over-unknown semantics defined then, not now.
