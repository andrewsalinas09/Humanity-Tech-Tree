# ADR-0037: Entailment is three-valued — SATISFIED / VIOLATED / UNKNOWN

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** external pre-build review, adopted by user; supersedes the "presumed-satisfiable" rule (TB-066 amended)

## Context
The permissive-monotone default said: a constraint referencing an undeclared attribute *passes* as presumed-satisfiable, labeled. That is a hand-rolled UNKNOWN rendered as YES-with-an-asterisk — and when the attribute is later declared and fails, the solver's answer flips YES→NO. The solver asserted a wrong YES: the prime directive (ADR-0015) violated at the entailment layer, the one place its litmus test was never applied. The stress test's skeptics defended the rule in the design's own vocabulary; an outside reviewer attacked the algebra instead and found it.

## Decision
1. **Every constraint check returns one of three values:** SATISFIED (declared value passes), VIOLATED (certain violation — declared value fails beyond uncertainty), UNKNOWN (attribute undeclared, or uncertainty ranges overlap the threshold).
2. **Kleene composition through requirement expressions:** AND — VIOLATED dominates, UNKNOWN dominates SATISFIED; OR — SATISFIED dominates, UNKNOWN dominates VIOLATED; NOT — swaps SATISFIED/VIOLATED, UNKNOWN stays UNKNOWN. **Vacuous** (H11: leaves pruned by exclusion) is *removal from the expression*, distinct from UNKNOWN (present, unresolved).
3. **The realizability lattice** replaces two-valued buildability: PROVEN_REALIZABLE / UNKNOWN (possibly realizable) / PROVEN_UNREALIZABLE. LOCKED / THEORETICAL / REALIZED become UI vocabulary derived from the lattice + facts.
4. **Gap lists are the UNKNOWN set, carried per-claim in every trace.** "Could Rome build X?" returns "not disproven — 14 requirements unresolved: [list]," never an accidental YES. This is what makes invention prospecting honest: hypothetical-tech chains are mostly UNKNOWN, the exact regime where two-valued collapse lies most.
5. **Presentation policy sits above the lattice:** the browse/fun view may render UNKNOWN optimistically ("possible so far"), the research view conservatively ("not proven"). Same entailment, two lenses (dual-audience, ADR-0033). UNKNOWN never blocks authoring — the lazy-attribute economy (TB-066's surviving half) is untouched.
6. **Monotonicity, restated correctly:** new facts move UNKNOWN → SATISFIED or VIOLATED; they never flip SATISFIED ↔ VIOLATED (only supersession of the underlying facts can). The solver can now never assert something it must later unsay.
7. **H2 is recognized as this rule's temporal special case** (certain-violation = VIOLATED; interval overlap = UNKNOWN). **TB-042's missing-node detector** fires only on PROVEN_UNREALIZABLE × validity=current_truth — UNKNOWN chains never raise false bounties.

## Why
Three states existed in reality; the algebra only had two, so absence of evidence leaked into YES. Making UNKNOWN first-class is the prime directive applied to solver outputs: incompleteness stays incompleteness all the way through composition, and every downstream mechanism (gap lists, bounties, prospecting, counterfactuals) gets sharper rather than more complex.

## Consequences
- SCHEMA constraint semantics + solver notes updated; constraint worked example and TB-066/TB-048 amended.
- The semantics kernel (roadmap) implements the lattice as its core; ~20 TESTBED cases become executable tests over it.
- Meta-lesson recorded: red teams inherit the document's framing; future stress tests should include reviewers briefed to attack the algebra, not the prose.
