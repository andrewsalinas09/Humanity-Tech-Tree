# ADR-0044: The UI stack — the tech tree rendered as a planet (MapLibre + tile pyramid + Next.js)

- **Status:** Accepted (user endorsed the hypothesis; research confirmed — `docs/research/2026-08-graph-rendering.md`)
- **Date:** 2026-08-08

## Decision
1. **Graph surface: MapLibre GL JS** consuming a **server-generated vector-tile pyramid** — nodes, edges, family bubbles, and density fields as MVT features; bulk pyramid as PMTiles on object storage + a small dynamic tiler for fresh edits. The ADR-0043 zoom tiers map 1:1 onto map layers: far = fill/heatmap density, mid = bubble features, near = circle/symbol/line layers with data-driven styling and feature-state dimming (presumptions, shadows).
2. **deck.gl interleaved via MapboxOverlay** as the near-zoom escape hatch: rich composite badges and bubble→children morph animations beyond sprite compositing. It augments before it could ever replace.
3. **App shell: Next.js, self-hosted, Redis cache handler from day one** — millions of crawlable node permalinks via on-demand ISR; no vendor lock (ADR-0043 §self-host).
4. **Retained from D1–D6:** React orchestrates and never renders the graph; ELK-class layered layout (server-side), Tailwind + shadcn-pattern components + the trust visual language as tokens; browser calls the same Service verbs through a thin JSON facade.

## Why this is correct-from-the-start (ADR-0043 test)
MapLibre is the only 2026 candidate whose architecture already streams billions of features to a bounded-memory client with smooth fractional zoom (the OSM planet is ~107 GB of PMTiles, rebuilt daily), and the only one with industrial **label collision/priority/zoom-reveal** — the part every graph library fails at. Production precedent: anvaka's Map of GitHub (690k-node graph as tippecanoe tiles in MapLibre). Academic precedent: the 2026 MSAGLJS tile-pyramid paper validates the exact browsing model with constant per-frame GPU load. Engine health: v5.19 (Feb 2026), funded org, WebGPU on the official roadmap. Rejected: Cytoscape (canvas-era ceiling — the convenience hack ADR-0043 forbids), Sigma v3/v4 (best glyphs, but the entire streaming/LOD/label layer would be ours to build), cosmos/G6/GraphGPU (wrong model or toy scale), fully-custom PixiJS (last resort).

## The three named risks (owned, not ignored)
1. **Living-graph tile generation is our unsolved hard part** — incremental re-tiling + layout stability under continuous edits has no published solution at this scale → **Q-22** (research stops at 33k nodes client-side; we own the frontier here).
2. **The coordinate contract is a day-one freeze:** the mapping of the abstract DAG layout into the bounded Mercator band + zoom↔LOD calibration must be fixed BEFORE the first production pyramid — changing it re-tiles the world. It joins the permanent contracts (fact log, verbs, tile protocol) in SCHEMA-level governance.
3. **Near-zoom styling ceiling:** composite trust badges and bubble-morph transitions are custom in every engine — prototype both early to calibrate when the deck.gl overlay engages.

## Consequences
- Build order for the viewer: coordinate contract spec → layout+tiler over the skeleton → PMTiles pyramid → MapLibre shell with the three tiers → trust-language styling → deck.gl overlay as needed → Next.js permalinks.
- Q-22 opened (incremental re-tiling / layout stability). The "Map of GitHub" and MSAGLJS papers are the study set.
