# ADR-0008: Lazy abstraction, link-as-low-as-possible, and widening via LCA

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
Should iPhone depend on "Processor" (abstract) or "ARM Cortex-A18" (specific)? Pre-building abstract layers "just in case" produces empty architecture-astronaut categories; linking too abstract loses historical truth.

## Decision
Link to the most specific leaf that is true. Create an abstract parent (interface/role node, e.g. "Mobile Processor") only when a second real implementation forces it — the refactor cost is paid exactly once, when reality actually diverges. Instances point down (iPhone 16 → Li-ion); abstract families are widened only as needed. Historical exceptions never delete a requirement — they *widen* it to the Least Common Ancestor, recorded as a `RequirementOverride {original, relaxed, justification}`. "Reality is the ultimate spec."

## Why
Avoids speculative structure while keeping every link true. Also yields free queries ("iPhone still points at ARM ⇒ all iPhones use ARM"). The LCA machinery doubles as a diagnostic — a "compiler for history" that explains invalid connections and offers quick-fixes (swap / reclassify / widen).

## Consequences
Editors need the Intercept/Abstract wizard verbs (ADR-0012) to perform these refactors safely. A garbage collector can collapse single-child abstractions back into their leaf.
