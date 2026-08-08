# ADR-0006: OPTIMIZES edges are existence dead-ends — this is what makes bootstrap loops legal

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest; README

## Context
Technology bootstraps itself: Iron → Steel → Bessemer Process → better Steel; CPU → Computer → EDA software → better CPU. Naively these are dependency cycles, which a DAG solver must reject.

## Decision
`OPTIMIZES` edges are ignored by existence/possibility traversal but traversed by cost/quality queries. Cycle detection rejects loops *except* through optimization edges. The solver resolves improvement loops generationally ("Temporal Leveling"): Gen-0 primitive output builds the optimizer, which upgrades subsequent output.

## Why
"If it optimizes something then it's not necessary to make it. If it was, it would just be makes_possible." This single rule makes bootstrap loops legal, terminating, and queryable — shortest-path answers "how was X first made," optimizer-traversing answers "how is X made well."

## Consequences
Every edge author must decide: enabling (MAKES_POSSIBLE-family) or improving (OPTIMIZES)? Getting it wrong either creates an illegal cycle (caught by the circuit breaker) or hides a real dependency.
