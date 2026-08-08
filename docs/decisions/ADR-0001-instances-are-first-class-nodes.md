# ADR-0001: Instances are first-class nodes, not sub-IDs

- **Status:** Accepted
- **Date:** ~2026-01 (pre-restart; see git commit "removed the sub id problem")
- **Source:** long-chat digest (`docs/archive/digests/2026-01-18-gemini-long-chat.md`)

## Context
Early designs gave product versions composite keys (`sub_id`) under a parent node, plus reference counting to compute whether an abstract node was "realized."

## Decision
Every version/instance is an ordinary node. Relationships are declared with `IS_TYPE_OF` / `IS_REFINEMENT_OF` edges. No composite keys, no reference counting.

## Why
Composite keys created a "shadow database" requiring special handling in every API. Reference counting created hidden *calculated* state that drifts. Edges *declare* reality instead of deriving it, are debuggable, and allow inserting nodes retroactively (add "DDR" between "RAM" and "DDR4" later without migrations).

## Consequences
Node count grows, so node creation needs an editorial gate — that's the Significance Filter (ADR-0009) and ProductIteration data records for minor versions.
