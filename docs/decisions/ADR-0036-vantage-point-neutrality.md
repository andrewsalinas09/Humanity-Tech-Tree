# ADR-0036: Vantage-point neutrality — the rules are viewpoint-blind; only facts dictate

- **Status:** Accepted
- **Date:** 2026-08-10
- **Source:** user directive, restart session 3 ("we cannot favor any vantage point. Only facts can dictate anything.")

## Context
The graph will host disputes: rival dating camps (Thera), rival historiographies (diffusion vs independent invention), rival ontologies (chemists' steel vs metallurgists' twelve steels), politically charged causality (suppression edges, colonial-era attributions). The moderation and trust systems must never become an editorial line.

## Decision
1. **Equal standing to author.** Every community, school, and individual operates under the identical rules: the same verbs, the same review process, the same citation requirements, the same ladder. No claim is pre-ranked by who asserts it; no group's nodes or edges are structurally privileged.
2. **Only facts dictate outcomes.** Where views compete, both are represented as parallel claims (the TB-009/Thera pattern: competing edges, each with its own citations, epistemic status, and computed confidence). What separates them downstream is exclusively what their evidence earns them through the ladder (ADR-0032) and the confidence formula (ADR-0033) — "they will get L# verification as the citations allow."
3. **Neutrality of rules, not of outcomes — no false balance.** The evidence machinery WILL rank claims: fringe ends up labeled fringe because its citations are weak, circular, or absent — by computation, never by decree. Displaying that ranking is not a vantage-point violation; suppressing it would be (ADR-0015: the graph must not launder weak claims as strong ones).
4. **Moderation adjudicates process, never truth.** Reviewers and circuit breakers act on structure, vandalism, citation presence, and rule compliance. "I believe this claim is false" is never grounds for rejection — the remedy for a believed-false claim is counter-evidence: citations, challenges, competing claims, and the formula doing its work.
5. **The formula and rules themselves are viewpoint-audited.** Because outcomes flow from the confidence formula and moderation parameters, those are the surfaces a vantage point would try to capture — which is why the formula is code-channel governed with public golden evals (ADR-0035 H15), independence is operator-level (H16), and every ranking is traceable to facts (ADR-0033 §4). Bias claims are answerable with traces, not assurances.

## Why
This is the prime directive's social corollary: a graph that favored a vantage point would be *asserting* something (the favored view's primacy) that is not a citable fact. Neutral rules + evidence-computed outcomes is also the only stable equilibrium for a community project — any editorial line invites capture wars over the line itself, whereas here the only way to win is to bring better sources.

## Consequences
- Dispute-resolution flows (Q-14) inherit this frame: they converge process, not verdicts — verdicts are computed.
- UI: competing claims render side by side with their bands and traces; no "official" position styling exists.
- TB-064 added.
