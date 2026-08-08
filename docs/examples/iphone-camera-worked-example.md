# Worked example: the iPhone camera — retroactive specialization

Companion to the 802.11 example. Tests the *consumer-side* question (TB-035): a role that was one thing splits when history makes a distinction important, without breaking or falsifying anything. Validates ADR-0020.

## Timeline of graph states

**2007 — one camera, one edge.**
`Camera Module IS_COMPONENT_OF iPhone (family)`. iPhone 1 inherits it (ADR-0019) and asserts its actual module; specs are attributes: `{resolution: 2MP, autofocus: false}`. No camera taxonomy exists because no distinction matters yet (lazy abstraction, ADR-0008).

**2010 — the front camera arrives. Reconciliation is two ADDS, zero edits:**
1. `Front-Facing Camera IS_TYPE_OF Camera Module` (new role — the distinction history just made important).
2. `Front-Facing Camera IS_COMPONENT_OF iPhone (family), start 2010.5` (dated family edge — contiguous era rule, ADR-0019 §4).

The original generic edge **stays untouched**: "iPhones have a camera" was true in 2007 and is true now. It continues as the zoomed-out truth; the new edge is higher resolution (ADR-0003). Nothing is archived because nothing was wrong — archiving/interception (ADR-0011/0012) is reserved for edges whose *target* was wrong for the claim, not for edges that gained more specific siblings.

**2019+ — many lenses, and a sub-family trick.**
- Roles: `Ultrawide Camera`, `Telephoto Camera` — `IS_TYPE_OF Rear Camera` (created only now, when the distinction pays rent).
- Telephoto is NOT true of all iPhones — but it IS true of all iPhone Pros. So: `iPhone Pro` sub-family node (`IS_TYPE_OF iPhone`), and the telephoto edge attaches THERE. Truth-granularity attachment (ADR-0018 §4) applied to product sub-lines. Non-Pro models need no exclusions because the edge never claimed them.
- Periscope telephoto (15 Pro Max only): instance-level edge — again, attach where true.

**Specs for purchase decisions.**
Focal length, aperture, sensor size: attributes on the module/edges (ADR-0004, Lazy Split — attributes until a supply chain diverges). `Sony IMX803` becomes a node only when its manufacturing lineage matters to someone (Manufacturing Test); until then `sensor_model` is an attribute value. Full per-model spec sheets = instance attributes + iteration records — the graph *permits* DigiKey-grade depth without ever requiring it.

## The principle this case adds (ADR-0020)

**Uneven resolution is normal and permanent.** A dashcam keeps its generic `Camera IS_COMPONENT_OF Dashcam` edge forever; iPhone gets the full tree because contributors care. Both are correct indefinitely. Depth is opt-in per node, demand-driven; the architecture's only obligation is to make arbitrary depth *possible* everywhere (roles + attributes + sub-families + iteration records already suffice).

## Honest caveat → Q-06

When a generic edge coexists with its specializations, component-counting queries must not double-count (generic "camera" + front + rear ≠ three cameras). This case is now the motivating example for the shadowing/subsumption decision (Q-06, TB-025).
