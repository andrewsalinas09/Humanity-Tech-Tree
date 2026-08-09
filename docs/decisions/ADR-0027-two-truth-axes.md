# ADR-0027: Two orthogonal truth axes; validity lives on both nodes and edges

- **Status:** Accepted (resolves Q-02)
- **Date:** 2026-08-08
- **Source:** user rulings via direct questions, restart session 2

## Context
Three partially overlapping truth systems had accumulated: ValidityStatus (nodes and edges), EpistemicStatus (edges), and a dropped ConfidenceLevel for dates. Their division of labor was never defined (Q-02).

## Decision
1. **Two orthogonal axes, kept separate:**
   - **Validity** — is the claim's *content* held true today? (current truth / disproven / superseded / hypothetical / subjective). Phlogiston: disproven.
   - **Epistemic** — how confident are we that the *assertion/record* is accurate? (mainstream fact / high confidence / debated / uncertain origin / fringe theory / mythology). Vikings reached America: valid AND merely high-confidence.
   - The proof they're orthogonal: phlogiston is epistemically well-documented (people really believed and recorded it) and invalid (disproven). Merging the axes cannot express that.
2. **Validity lives on nodes AND edges.** Node validity filters concepts (dim/hide disproven beliefs); edge validity marks disproven mechanisms between valid nodes ("Miasma → causes → Disease" is a disproven claim; the Disease node is fine).
3. **Epistemic stays edge-level** (it qualifies claims); a node's overall epistemic texture emerges from its edges.
4. **Date confidence stays numeric** (`uncertainty_range` on DatePoint) — the dropped ConfidenceLevel enum stays dead.
5. **Presumption (ADR-0019) is derived, never stored** — it's an entailment (ADR-0026), not a fourth truth field.

## Why
Both axes are ground facts about mainstream assessment — citable, so ADR-0026-legal. Everything else truth-adjacent is either numeric fact (uncertainty) or entailment (presumption), so the truth system is now closed: exactly two stored axes, everything else computed.

## Consequences
- Q-02 → Resolved. TB-009's caveat clears.
- Viewer filter model: two independent sliders/filters (validity, epistemic) instead of one confusing merged scale.
