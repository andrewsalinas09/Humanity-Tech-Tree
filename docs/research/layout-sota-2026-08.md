# SOTA research: drawing the graph (2026-08-09)

Three parallel research tracks (layered-layout algorithms; production graph-as-map systems; edge routing & readability), run after the user's verdict that the map still looks "VERY messy" and that graph drawing is make-or-break for the product. Full agent reports summarized; all claims carry sources.

## The diagnosis: our hand-rolled pipeline has three textbook defects

Our current layout (longest-path layering → barycenter sweeps → force relaxation) fails in ways each *individually documented* in the literature:

1. **Longest-path layering is the known-worst layering heuristic.** It jams nodes to extreme layers (why our leaves pile in the top strip) and maximizes edge spans, which maximizes crossings. Graphviz replaced it with **network-simplex layering** in 1993 (Gansner et al., TSE93). ELK treats longest-path as the cheap fallback only.
2. **Barycenter sweeps without the `transpose` refinement plateau early.** dot's mincross = weighted-median sweeps + adjacent-pair-swap transpose after every sweep, with restarts, keep-best.
3. **Force relaxation as coordinate assignment is actively harmful.** No production layered engine (dot, ELK, OGDF, yFiles) uses physics for final coordinates — springs re-tangle the computed ordering and make spacing degree-dependent. The correct phase-3 is **Brandes–Köpf horizontal coordinate assignment** (use the 2020 erratum, arXiv:2008.01252): linear-time, zero new crossings, long edges become straight verticals, even spacing by construction.

Also empirically wrong in our rendering:
- **Uniform edge curvature measurably hurts readability** (Xu et al., TVCG 2012); our bezier arcs + deterministic jitter are the studied anti-pattern — jitter manufactures glancing-angle crossings, and **crossing angle (not count) is the dominant readability cost** (Huang et al., eye-tracking).
- **Edge bundling (FDEB/KDEEB-style) is disqualified for this product**: studies show it destroys node-to-node path tracing (AVI 2012) and creates "independent edge ambiguity" — viewers infer connections that don't exist. Tracing to first principles is the product; never density-bundle. (Exceptions if ever needed: Edge-Path Bundling — bundles follow real dependency paths — or Pupyrev-style ordered bundles.)

## The unanimous production patterns (every beautiful graph-map does these)

Surveyed: Anvaka's map-of-github, GraphMaps (MSR — the academic system closest to ours; arXiv:1506.06745, 1705.05479), GMap/gvmap countries, Nomic Atlas, Paperscape, Open Syllabus Galaxy, VOSviewer science maps, plus game tech trees (Civ, PoE, Factorio).

1. **At rest, a beautiful graph-map is a labeled dot-density map with regions — edges are an interaction, not a base layer.** map-of-github, Paperscape, Atlas, Galaxy: none draw edges at rest; connections appear on hover/click (degree-of-interest theory: van Ham & Perer 2009). Factorio's devs concluded the same: draw only the selected node's subgraph.
2. **Mental-map invariant: positions never change with zoom.** Only existence, aggregation, and labels change per zoom. GraphMaps formalizes *monotone persistence*: a node visible at z4 is visible at z10, in the same place, with per-tile entity quotas.
3. **Two-phase hierarchical layout**: cluster/corridor macro-graph laid out first, contents laid out inside fixed frames (anvaka's two-phase force; ELK top-down layout; embarrassingly parallel at scale).
4. **Regions ("countries") instead of inter-cluster edge ink** — GMap/gvmap Voronoi-merged countries with wiggly borders; MapSets for contiguity guarantees. Corridors can literally be countries with names.
5. **Hierarchical labels by zoom** (continents → countries → cities), collision handled by the map engine; fade, never pop.
6. **Game tech trees are hand-laid** (Civ VI: algorithmic column, manual `UITreeRow` lane per tech). The stealable ideas: rank bands as hard columns, few lanes, a per-node manual nudge field for the 5% the algorithm fumbles, uniform node capsules. Community-consensus warning: a Civ-style lattice "stops being readable around thirty techs" — the global view must not be a lattice.

## Edge-drawing recipe (when edges are shown)

Ranked by impact/effort (all at tile-build time, never at serve time):
1. Delete jitter; near-straight polylines with rounded bends only where they encode something.
2. **Ports**: edges leave provider's bottom, enter consumer's top, spread across the node span in barycenter order (ELK FIXED_ORDER behavior).
3. **Fan-in combs**: >2 edges at a node merge into a short trunk + symmetric comb (~1 node-height) — local bundling that's unambiguous because edges truly share the endpoint (yFiles bus-routing, dot `samehead` spirit).
4. **Dummy-node corridors** (dot's core trick): layer-spanning edges get real x-positions in every layer they cross and the final spline is routed through them — reserved vertical channels; node-edge overlaps become structurally impossible when routed against inflated obstacles.
5. **Casing**: each edge = background-color wider line + fill line (two MapLibre layers) so crossings read as over/under, the cartographic road-crossing trick.
6. **Direction = taper** (wide at provider, narrow at consumer; Holten & van Wijk CHI 2009: tapered beats arrowheads); arrowheads only on hover/selection.
7. Per-zoom edge sets re-routed against that zoom's obstacle set (sleeve-routing tile-pyramid paper, arXiv:2605.17498 — the published system closest to our architecture).

## Engines (server-side)

| Option | Verdict |
|---|---|
| **Graphviz `dot -Tjson`** (via pygraphviz) | Reference-quality full pipeline incl. spline routing around nodes; trivial to call; ~10^3–10^4 nodes per invocation. **Fastest path to quality now.** |
| **ELK** (headless Java / elkjs in Node) | Best open-source layered engine; ports, compound/top-down layout, interactive (stability) modes, 140+ options. The long-term engine. |
| OGDF (C++), rust `fast-sugiyama`, grandalf (py) | Own-the-internals options; grandalf prototype-only. |
| Stress/SGD family (DiG-CoLa, WebCola, s_gd2) | Respects layering via constraints but no crossing minimization; use only as macro-graph/extreme-scale coarse layout. |
| dagre | Weakest Sugiyama implementation; avoid. |

Scale path (10^6+): no million-node Sugiyama exists; the answer is hierarchical decomposition (corridor macro-graph → per-corridor layered layout in fixed frames, parallel) + GraphMaps-style per-zoom content selection — same shape as Phase B below. Stability under edits (Q-22): DynaDAG/North-Woodhull incremental Sugiyama + ELK INTERACTIVE strategies + model-order determinism (Domrös 2023/24); insert new nodes at neighbor-median in their layer, local transpose repair, full relayout only at versioned epochs.

## User rulings (2026-08-09)

1. **Engine: Graphviz dot now — but we will (99%) hand-implement the pipeline ourselves later.** dot's role is to teach us what *correct* looks like; it is the reference/benchmark, not the destination. Positions are derived data (ADR-0026) so the swap is free.
2. **Edges: faint at rest, vivid on focus** (the unanimous production pattern).
3. **Scope: Phase A + corridor countries** in this pass.

## Proposed plan (staged; discussed with user before implementation)

- **Phase A — reference-quality drawing at dev scale:** replace the hand-rolled layout with `dot` (or ELK) called server-side, mapped into the lat/lng world contract (foundations top). Kill jitter/curvature; ports + combs + casing + taper. Edge-visibility policy decision (edges-at-rest vs on-focus) is a product call → user.
- **Phase B — map structure:** corridor countries (Voronoi-merge regions), two-level layout, per-tile budgets with monotone persistence, hierarchical labels.
- **Phase C — scale & stability:** determinism contract, incremental insertion, epoch relayouts, per-zoom edge routing.

Key sources: Gansner et al. TSE93 (dot) · Brandes–Köpf 2001 + erratum arXiv:2008.01252 · ELK Layered reference · GraphMaps arXiv:1506.06745 + 1705.05479 · sleeve routing arXiv:2605.17498 · map-of-github repo · gvmap/GMap · MapSets · Xu et al. 2012 (curves) · Huang et al. (crossing angles) · Holten & van Wijk 2009 (taper) · AVI 2012 (bundling harms tracing) · van Ham & Perer 2009 (DOI) · Domrös 2023 (model order) · DynaDAG/North-Woodhull (incremental).
