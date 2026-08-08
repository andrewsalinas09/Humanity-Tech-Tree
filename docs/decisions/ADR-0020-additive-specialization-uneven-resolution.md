# ADR-0020: Specialization is additive; uneven resolution is normal

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user edge case (iPhone front camera, TB-035); worked example `docs/examples/iphone-camera-worked-example.md`

## Context
When history makes a new distinction important (front vs rear camera, 2010), the graph already contains a coarser edge ("iPhone → Camera") authored before the distinction existed. How does the architecture reconcile without breaking anything? And: most nodes will never get fine-grained treatment — is that a defect?

## Decision
1. **Specialization is additive.** When a role splits, the reconciliation is: add the sub-role node(s) (`IS_TYPE_OF` the original) and add edges at whatever granularity the new distinction is true (dated family edge, sub-family edge, or instance edge — ADR-0018/0019 rules). The original generic edge is **never archived or edited if it remains true** — it persists as the zoomed-out truth (ADR-0003). Archiving/interception (ADR-0011/0012) is reserved for edges whose *target was wrong for the claim*, not edges that gained more specific siblings.
2. **Sub-families are ordinary nodes.** A trait true of a product sub-line but not the whole family (telephoto ↔ iPhone Pro) attaches to a sub-family node (`iPhone Pro IS_TYPE_OF iPhone`), created lazily like any abstraction. No exclusions needed on the models the edge never claimed.
3. **Uneven resolution is normal and permanent.** Depth is opt-in per node, demand-driven; a dashcam's generic camera edge and iPhone's full multi-lens spec tree are both correct indefinitely. The architecture's obligation is to make DigiKey-grade depth *possible* everywhere (roles + attributes + sub-families + iteration records), never to require it anywhere.

## Why
Pure composition of existing rules — additive refinement follows from the prime directive (the coarse claim stayed true; new structure only raises resolution), and lazy sub-role/sub-family creation is ADR-0008 applied at the moment reality diverges. Stating it as policy prevents the destructive instinct ("fix" the old edge when a distinction appears), which would churn history and violate ADR-0011 for no gain.

## Consequences
- Editing wizards offer "Specialize" as an additive operation (add sub-role + granular edges), distinct from "Intercept" (which archives a wrong-granularity edge).
- Generic + specialized edge coexistence makes Q-06 (shadowing/subsumption for counting queries) more urgent; this case is its motivating example.
- TB-035 → Solved (design).
