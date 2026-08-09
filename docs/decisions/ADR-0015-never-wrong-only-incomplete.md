# ADR-0015: The prime directive — the graph can never state wrong information, only incomplete information

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user, restart session 2 (generalizing ADR-0003 and the "Lazy Split" principle)

## Context
At tens of millions to billions of nodes, mistakes are unfindable and migrations are near-impossible. The project is only viable as a citable, reliable community database — one demonstrated falsehood costs more trust than a thousand gaps.

## Decision
Every schema construct and every editorial rule must satisfy: **any state the graph can be in is true; what varies is resolution.** Incompleteness is always legal; wrongness must be inexpressible wherever the schema can enforce it. Litmus test for any design proposal: "can this construct ever *assert* something false, or only omit something true?"

## Why
This is already the hidden principle behind the strongest existing decisions: technically-true edges + pruning (ADR-0003), zoomed-out links awaiting intermediate nodes, Lazy Split (a generic node is never wrong, a premature split can be), stub nodes, state-as-query (stored state can be stale ⇒ wrong; computed state can't), regional timelines (a single global date is usually false somewhere), widening-not-deleting (ADR-0008), and no-deletion versioning (ADR-0011). Naming it as the prime directive makes it the acceptance test for every future mechanism.

## Consequences
- Every TESTBED case gains an implicit second check: does the mechanism's failure mode produce *wrongness* or *incompleteness*? Only the latter is acceptable.
- Uncertain content must be stored as uncertain (epistemic status, uncertainty ranges) rather than rounded to a clean false claim.
- Anything subjective (impact_weight) must be labeled as such, never presented as fact.
