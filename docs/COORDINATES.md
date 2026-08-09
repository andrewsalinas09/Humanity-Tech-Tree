# The Coordinate Contract (v1 — PROPOSED; freezes before the first production pyramid)

The mapping from the abstract graph to the tile world (ADR-0044 risk #2). Iterable during dev (re-tiling a dev graph is free); **frozen at first production bake** with user sign-off. Everything downstream — tiles, URLs-with-viewport, screenshots, muscle memory — depends on it.

## The world

The graph lives on a Web-Mercator world (so every map tool on earth works unmodified):
- **Latitude = dependency altitude, foundations at the TOP** (user ruling, v1.1): natural laws, raw materials, and the deep old things at the north; technology *descending* as it composes — consumers hang below their providers, and the iPhone sits at the bottom of everything it rests on. Band: lat ∈ [−75°, +75°], layer bands by longest-provider-path depth.
- **Longitude = domain neighborhoods.** Within a layer, nodes are ordered by provider barycenter (children near their parents' meridians), so lineages form vertical corridors — metallurgy runs as a corridor, computing as another. lng ∈ [−179°, +179°].
- **Positions are served data with a stability goal, never truth** (ADR-0026: derived, rebuildable). Layout stability under edits is Q-22; v1 uses deterministic full relayout (acceptable at dev scale, noted).

## Zoom ↔ LOD calibration (the three tiers, ADR-0043 D1)

| Zoom | Tier | Renders |
|---|---|---|
| z0–z4 | continent | density fields + the great corridor structures (server-aggregated) |
| z5–z9 | city | family bubbles (ADR-0018 LOD), major nodes, corridor labels |
| z10+ | street | individual nodes with the full trust language + edges + labels |

Dev-scale graphs render fully at all zooms; the thresholds live in the style, not the data.

## Tile scheme (the permanent protocol)

Standard XYZ Web-Mercator tiles, MVT (extent 4096). Layers:
- **`nodes`** — point features: `node_id, name, category, validity, cited (bool), vouched (bool), band, zoom_min`
- **`edges`** — line features: `edge_id, type, qualifier, shadowed (bool), from, to`
- **`bubbles`**, **`density`** — reserved (family-bubble polygons; aggregate heat), same contract, populated when scale demands.

Served by the **dynamic tiler** (live from the store); the **PMTiles bulk pyramid** is the identical contract baked ahead — the ADR-0043-legal modest start.

## The trust visual language (tokens; D5 — v1.1 rulings)

- **White world**; **nodes are little books** (rounded rects slightly wider than a book, category-tinted SDF glyphs) — not circles.
- **Red ring** = uncited (`cited=false`, computed — ADR-0030)
- **Faded book** = validity unassessed (nobody vouched — ADR-0042); hypothetical slightly less faded
- **Focus dimming**: selecting a node dims everything outside {self, parents, children} and non-incident edges to near-transparency (feature-state driven)
- **Ghosted dash** = shadowed edge (ADR-0021) · **Yellow accents** = UNKNOWN gap lists (ADR-0037)
- ASSOCIATION/SUCCEEDS hidden by default (ghost layer), History Mode reveals.
- Chrome: info panel LEFT, tabs on top (Explore/Bounties/Tickets/Changes), search upper-right.
