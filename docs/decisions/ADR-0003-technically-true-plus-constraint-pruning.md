# ADR-0003: Technically-true edges are always valid; constraints prune to realistic paths

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** README brain-dump; both chat digests

## Context
An iPhone *could* theoretically be built with vacuum-tube logic. Forbidding such edges requires manually policing millions of judgment calls; allowing them unfiltered produces absurd paths.

## Decision
Any edge that is technically true is correct graph content — it just "lacks resolution." Attribute constraints on consumer edges (size, switching speed, power) prune infeasible paths at query time, forcing the realistic (state-of-the-art) route. If constraints eliminate every path, the node becomes *unrealized* and is surfaced as a public bounty.

## Why
"The Truth never changes; the Resolution just increases." This makes the graph monotonically improvable: contributors insert intermediate nodes and constraints instead of deleting "wrong" edges, and correctness emerges from physics-like properties at the seams (e.g. one Switching Speed attribute kills the vacuum-tube iPhone) rather than from manual bans. Gatekeeper nodes (IC, High-Pressure Vessel) encode era boundaries topologically for free.

## Consequences
The solver must evaluate constraints during traversal. Vandalism/nonsense detection shifts to the moderation layer (ADR-0013), not edge legality. Flag-and-fix becomes a gameplay loop.
