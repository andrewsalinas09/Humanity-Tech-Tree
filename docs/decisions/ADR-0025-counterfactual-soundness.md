# ADR-0025: Counterfactual soundness — possibility propagates only through necessary dependencies

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user, restart session 2 ("could we have had steam engines in Roman times? Maybe — but not if we depend on an 1800 paper for no reason")

## Context
A core use of the graph is counterfactual history: when COULD something have existed, and what actually gated it? The trap is the **false time-lock**: anchoring a technology to a dated work (Watt's paper, Einstein's 1905 papers) makes the counterfactual return "impossible before that date" for a contingent reason. Works have their own dependencies — the papers *could* have been written earlier if their inputs existed; only those inputs are real gates.

## Decision
1. **Two date computations, never conflated:**
   - **Actual date** — when it DID exist: recorded dates + regional timelines; the Did-Happen layer (works, people, orgs) fully participates.
   - **Earliest-possible date** — when it COULD exist: MAX over *necessary* dependencies only (concepts, capabilities, materials, techniques), evaluated against a chosen region/time knowledge state. The traversal **never passes through WORK_PUBLICATION or BIOLOGICAL_ENTITY nodes** — they are contingent anchors, not gates. (Extends ADR-0007's "possible when its Physics are met, not when its Author is born" from people to works.)
2. **Linter rule (the "1800 paper for no reason" guard):** an ENABLES edge from a WORK_PUBLICATION into the necessary layer is flagged — "depend on the concept this work codifies, not the paper." Works enrich history; they never lock possibility.
3. **Person time-bounding stays a Did-Happen-layer validation:** BIOLOGICAL_ENTITY receives ENABLES only from knowledge/concepts (the Einstein-in-1000BC anachronism check), and that check runs on the history layer — it validates recorded history, it does not constrain counterfactuals.
4. **Counterfactual queries are a signature capability:** "Could Rome have had steam engines in 100 AD?" = evaluate necessary deps against Rome's regional knowledge state; the answer is a gap list ("missing: precision boring, pressure-vessel metallurgy"), never a date sourced from contingent history.
5. **Earliest-possible is computed, never authored.** No field stores it; the solver derives it fresh from the graph at hand on every ask (same rule as node state, ADR-0002). It therefore improves automatically as the graph improves and can never go stale.
6. **The counterfactual query is the graph's debug harness.** Ask → answer → trace why/why-not → judge whether the trace is logical. An absurd answer is a *diagnosis*, not just an error: it localizes a missing constraint, edge, or node (this is literally how the need for attribute constraints was discovered — the vacuum-tube iPhone trace). Absurd traces are flaggable and feed the bounty loop: the graph tests itself through use.

## Why
The graph's counterfactual value depends entirely on keeping necessity and contingency separate. Any leak of contingent dates into possibility propagation silently poisons every "what if" query — and at scale nobody would notice which answers were poisoned. This is the prime directive applied to modality: asserting "impossible before 1800" because of a paper is *wrong information*; "not realized until 1800, possible earlier given X and Y" is the truth.

## Consequences
- The solver carries two traversal modes with different node-category masks; the KNOWLEDGE_REQUIREMENT→ENABLES collapse (Q-21) stands, with masks doing the work the special type once implied.
- ARCHITECTURE signature queries gain the counterfactual query. TB-040 added.
- Authoring guidance: necessary-layer deps target concepts/capabilities; works attach via the story layer (codifies/authored qualifiers).
