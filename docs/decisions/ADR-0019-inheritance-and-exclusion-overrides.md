# ADR-0019: Family edges are inheritable defaults; instances may widen OR exclude them

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user edge case, restart session 2 (iPhone-without-WiFi / front-camera case, TB-034)

## Context
Abstract-level edges ("iPhone → Camera", "iPhone → 802.11") state family-granularity truths that instances inherit. ADR-0008 covered instances that satisfy an inherited requirement *differently* (widening to the LCA). Uncovered: an instance that lacks the family feature entirely. The tempting tool — ADR-0017's NOT — is semantically wrong: `NOT(camera)` asserts "requires the absence of a camera" (a camera existing would make the instance impossible), whereas the need is "does not inherit this edge."

## Decision
1. **Family edges are inheritable defaults.** An instance's effective dependencies = inherited family edges + its own edges, modified by its overrides.
2. **Two override kinds, one mechanism** (`InheritanceOverride`): **WIDEN** — relax an inherited requirement to the LCA (subsumes ADR-0008's RequirementOverride); **EXCLUDE** — the inherited edge does not apply to this instance. Both carry a human justification.
3. **Inherited-but-unasserted facts are *presumptions*.** Queries and UI must distinguish "asserted at this instance" from "presumed via inheritance." An unrecorded exception therefore renders as a labeled presumption — incompleteness, never a false assertion (ADR-0015). Recording the exclusion is a resolution increase.
4. **Contiguous eras use dated edges, not exclusions.** "Front Camera IS_COMPONENT_OF iPhone from 2010" handles the 2007–2010 gap; exclusions are for scattered/non-contiguous exceptions (the GoPro shape). Below node granularity, iteration records may carry exclusions too, lifting per ADR-0018.
5. **NOT ≠ exclusion**, documented: NOT (ADR-0017) is a requirement about the world ("requires absence"); EXCLUDE is a statement about inheritance ("this default doesn't apply"). Editors and wizards must never offer NOT where EXCLUDE is meant.

## Why
Per-instance variation (iPhone 10 → 802.11ac, iPhone 18 → 802.11be, Sony vs Canon sensors) already worked via ADR-0008/0018 — instances link to their specific truths while the family links to roles/roots. Absence was the one uncovered direction, and exclusion completes the override algebra symmetrically (widen = relax, exclude = subtract) without touching edge semantics or monotonicity. The presumption label is what reconciles inheritable defaults with the prime directive.

## Consequences
- `Node.cpp`: `InheritanceOverride {family_edge_id, kind, relaxed_target_id?, justification}` on nodes; formalizes ADR-0008's override record in code for the first time.
- Solver/queries evaluate: own edges ∪ inherited edges − exclusions, with widenings applied; presumption status propagates to results.
- TB-034 → Solved (design). Viewer must render presumed vs asserted distinctly (e.g. dimmed inherited edges).
