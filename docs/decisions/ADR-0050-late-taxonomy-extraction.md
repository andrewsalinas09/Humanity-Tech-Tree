# ADR-0050: The late-arriving taxonomy parent — sibling linter + extract_family

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user edge case ("I add Samsung Galaxy, later someone realizes Phone isn't here — iPhone and Galaxy share everything. How does that work?") + rulings (auto-post self-bounties; grouped bulk hoist choice, information never lost)

## Context
Lazy Split (ADR-0004) blesses the flat state: siblings wired directly to shared providers are TRUE, indefinitely. But the graph should notice the Smartphone-shaped hole and heal when someone acts. Detection can't happen at propose-time (the new node has no edges yet — though the ADR-0048 semantic lane already surfaces the sibling as a high-similarity non-duplicate); the signal exists only post-wiring.

## Decision
1. **The sibling-cluster linter files bounties on the graph itself:** nodes sharing ≥ N providers (default 5, tunable) with no common taxonomy parent trigger a WANT_NODE request — *"Taxonomy parent for A + B"* — auto-posted by the `linter` system identity (ADR-0046 kind=system: even the linter is a blameable author), with the shared-provider list as evidence. Deduped against open requests; goes quiet once a common parent exists. Structural debt flows through the same queue as human asks.
2. **`extract_family(parent, siblings)` — a deterministic compiler** (ADR-0040): computes the shared claims across ALL siblings and opens ONE Decision ticket presenting them **grouped by provider category for one-glance bulk selection** (user ruling: "everything goes — or everything except glass screen"): options hoist_all / hoist_except[...] / hoist_only[...] / hoist_none. The pick and its justification are recorded forever (ticket resolution + CR notes).
3. **The heal compiles entirely to existing mechanics:** IS_TYPE_OF classify edges for the siblings; hoisted claims become family edges on the parent (inheritable defaults, ADR-0019 — both siblings now *presume* them); covered instance edges get `shadowed_by=[family edge]` — history preserved as dashed coverage, never deleted. Non-hoisted claims (glass) stay asserted at instances. Additive + shadowing throughout: never wrong, order-independent.

## Consequences
- TB-071 (Samsung Galaxy late parent) added and Solved; acceptance test runs the full loop: flat wiring → linter bounty → ticket → hoist-except → inheritance + shadowing → linter silent.
- The linter runs on tile-state rebuild (dev); at scale it moves to the apply pipeline with incremental pair checking.
- Future linters follow the same pattern (the graph as its own bounty poster): redundancy (L8), missing descriptions, uncited-cluster sweeps.
