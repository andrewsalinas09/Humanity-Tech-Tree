# Graph Rendering Technology Research — August 2026

**Context:** Renderer selection for the Humanity Tech Tree per ADR-0043 (map-tile LOD: server-computed
aggregate tiles at far zoom → family-bubble clusters at mid zoom → individual styled nodes at near
zoom; layered/DAG layout computed server-side; client budget ~10–100k renderable elements; smooth
continuous "street-view" zoom over an eventually billion-node graph).

**Method:** Web research conducted 2026-08-08 (WebSearch/WebFetch of primary sources). All claims
cited inline.

---

## 1. Renderer engines, state of August 2026

### 1.1 MapLibre GL JS (WebGL2 vector-tile map renderer, "abused" as graph surface)

- **What it is:** TypeScript vector-tile renderer (Mapbox GL JS v1 fork, BSD-3-Clause). Renders
  styled vector tiles with GPU acceleration, continuous fractional zoom z0–24, rotation, pitch.
  https://maplibre.org/maplibre-gl-js/docs/ · https://github.com/maplibre/maplibre-gl-js
- **Health (2026):** Very strong. v5.18/v5.19 shipped Feb 2026; monthly newsletters; funded
  organization with paid maintainers. https://maplibre.org/news/2026-03-03-maplibre-newsletter-february-2026/
- **WebGPU:** A WebGPU rendering backend is on the official roadmap and in progress alongside a
  modernized WebGL2 path (UBOs, immutable textures) — meaning the engine's future is not tied to
  WebGL. https://maplibre.org/roadmap/maplibre-gl-js/graphics-modernization/
- **Max practical element count:** Bounded by *viewport*, not dataset — this is the whole point.
  Vector-tile pyramids serve planet-scale data (OSM planet ≈ 107–120 GB PMTiles, billions of
  features) while the client only ever holds visible tiles. https://docs.protomaps.com/pmtiles/
- **Styling:** Data-driven style expressions (color/size/opacity by feature property or zoom),
  sprite-atlas icons (= color badges and band glyphs), `feature-state` for hover/dim without
  re-tiling, line layers with width/dash/gradient (= edge types), fill layers (= bubbles,
  density polygons). https://maplibre.org/maplibre-style-spec/layers/
- **Zoom/pan quality:** Best in class — inertial pan, fractional zoom, per-zoom interpolated
  styling, automatic symbol fade-in/out. This *is* the Google-Maps zoom feel the ADR asks for.
- **Custom tile sources:** Native. Any XYZ/TileJSON endpoint, or PMTiles single-file archives on
  static object storage via HTTP range requests (zero tile server to operate).
  https://protomaps.com/ · https://til.simonwillison.net/gis/pmtiles
- **Labels:** Native collision engine — see §3. No other candidate has this.
- **React:** `react-map-gl` (vis.gl) and `@vis.gl/react-maplibre` wrappers; also trivially wrapped
  by hand (imperative map in a ref'd div). https://maplibre.org/maplibre-gl-js/docs/plugins/
- **Proven as a graph surface:** anvaka's **Map of GitHub** — 690k+ repositories laid out by
  similarity, converted to GeoJSON, tiled with tippecanoe, rendered entirely in MapLibre with
  labels, cluster borders, and search. Author: "didn't want to reinvent the wheel, so ended up
  using maplibre." MIT. https://github.com/anvaka/map-of-github · https://anvaka.org/map-of-github/
  Map of Reddit is the same pattern. https://github.com/anvaka/map-of-reddit
- **Gaps for our use:** No graph semantics (neighbor highlighting across tile boundaries, edge
  traversal); rich composite node glyphs limited to sprite compositing unless we add a custom
  layer; bubble→children morph animation must be custom; abstract layout must be mapped into Web
  Mercator coordinate space (see risks, §5).

### 1.2 deck.gl (+ TileLayer) — WebGL2/WebGPU-transitional layer framework

- **What it is:** vis.gl / OpenJS Foundation layered GPU visualization framework. v9.x is built on
  luma.gl v9 whose core API is portable across WebGL2 and WebGPU; WebGPU backend exists but is
  explicitly **not production ready** in deck.gl as of now. https://deck.gl/docs/whats-new ·
  https://deck.gl/docs/developer-guide/webgpu · https://openjsf.org/blog/deckgl-v9
- **TileLayer:** First-class tiled loading — `getTileData` callback per tile, `renderSubLayers`
  to render each tile's payload with any layer, `visibleMinZoom`/`visibleMaxZoom` for LOD bands.
  Designed exactly for "datasets so big they cannot fit in browser memory."
  https://deck.gl/docs/api-reference/geo-layers/tile-layer
- **Max practical element count:** Millions of instanced primitives per frame (Scatterplot/Line/
  Icon layers); the tile pyramid bounds what's resident.
- **Styling:** Fully programmable — accessors per datum, custom layers with your own shaders.
  Strictly more flexible than MapLibre style spec (composite badges, arbitrary glyph shaders).
- **Labels:** TextLayer + CollisionFilterExtension — works but immature vs MapLibre (§3).
- **React:** First-class (`<DeckGL>`), and **interleaves with MapLibre** in the same WebGL context
  via MapboxOverlay — the two are designed to be combined. https://deck.gl/docs
- **Academic precedent:** *"Browsing Large Graphs with Tile Pyramids and Sleeve Routing in the
  Browser"* (arXiv 2605.17498, 2026) — MSAGLJS renders a precomputed graph tile pyramid through
  deck.gl's standard TileLayer: PageRank-guided node selection per level (top |V|/2^k nodes at
  depth k), per-level edge rerouting, ≤500 elements/tile budget, cross-fade between levels,
  ~60 Hz browsing with max ~2,567 objects/frame **independent of total graph size**. Their
  pyramid is built client-side (limit ~33k nodes, minutes of preprocessing) — but the *browsing*
  architecture is exactly ADR-0043 with server-side generation swapped in.
  https://arxiv.org/html/2605.17498
- **License/health:** MIT, OpenJS Foundation, large corporate user base (Foursquare/CARTO/Uber
  lineage). Healthy.

### 1.3 Sigma.js v3 / v4-beta (WebGL graph renderer)

- v3 stable, MIT, backed by OuestWare + Sciences Po médialab; powers Gephi Lite v1.0 (Oct 2025).
  v4 is in beta with a GPU-accelerated rendering pipeline. https://www.sigmajs.org/ ·
  https://v4.sigmajs.org/ · https://gephi.wordpress.com/2025/10/08/gephi-lite-v1/ ·
  https://github.com/jacomyal/sigma.js/discussions/1469
- **Max practical:** ~100k edges with default styles; degrades to ~5k nodes when every node has
  an icon/pictogram program. https://doc.linkurious.com/ogma/latest/compare/sigmajs.html
  Within our ≤100k-element client budget — workable but with little headroom for styled nodes.
- **Styling:** Best pure-graph ergonomics of any candidate: pluggable node/edge "programs" —
  `@sigma/node-image`, `NodePictogramProgram`, `@sigma/node-piechart`, `@sigma/node-square`,
  `@sigma/edge-curve`; custom label/hover draw functions.
  https://www.sigmajs.org/docs/advanced/customization/ · https://www.npmjs.com/package/@sigma/node-image
- **Tiles/LOD:** None. Camera is not tile-aware; no streaming source concept. Gephi Lite loads
  whole graphs in memory (graphology model). We would build the entire tile loader, LOD
  scheduler, and label collision ourselves.
- **React:** `@react-sigma` ecosystem; fine.
- **Verdict:** Excellent *near-zoom node program* library; wrong chassis for planet-style tiling.

### 1.4 Cytoscape.js

- Canvas-based; a **WebGL renderer preview** landed in v3.31 (Jan 2025), with the team candid
  that text and edge rendering remain the bottlenecks. Practical interactive ceiling is in the
  low tens of thousands of styled elements. https://blog.js.cytoscape.org/2025/01/13/webgl-preview/ ·
  https://github.com/cytoscape/cytoscape.js/discussions/3088
- Strong graph-theory API (traversals, selectors), MIT, healthy academic backing — but the
  renderer is a decade behind the requirement. **Rejected** as surface; possibly useful headless
  for graph ops (though graphology covers that lighter).

### 1.5 cosmos.gl / Cosmograph (GPU force layout + rendering)

- cosmos.gl v3 (OpenJS incubation, MIT, 1.2k★): all simulation *and* drawing in shaders; luma.gl
  WebGL2 backend; hundreds of thousands to ~1M points in real time. Accepts **precomputed
  positions** via `setPointPositions(Float32Array)` — so it can render our server layout, not
  just force layouts. No tiling, no real label system. https://github.com/cosmosgl/graph ·
  https://openjsf.org/blog/introducing-cosmos-gl
- **Verdict:** Wrong layout model (force) and no LOD streaming; its GPU buffer-oriented pipeline
  is a useful design reference for a custom near-zoom layer, nothing more.

### 1.6 AntV G6 5.x

- Feature-rich graph framework on @antv/g with Canvas/SVG/WebGL renderers, Rust/WASM + WebGPU
  layout acceleration, React-node support, Graphin React toolkit. MIT.
  https://g6.antv.antgroup.com/en/manual/whats-new/feature · https://github.com/antvis/G6
- Performance posture is "optimize interactions on a few-thousand-to-tens-of-thousands element
  canvas" (e.g., `OptimizeViewportTransform` hides elements during pan to keep FPS).
  https://g6.antv.antgroup.com/en/manual/behavior/optimize-viewport-transform
- No tile pyramid concept; dashboard-scale, not planet-scale. **Rejected.**

### 1.7 PixiJS v8 (custom build substrate)

- v8.16 (2026): mature dual WebGL2/WebGPU renderer, though the team still recommends WebGL for
  production; excellent sprite batching. https://pixijs.com/blog/8.16.0 ·
  https://pixijs.com/8.x/guides/components/renderers
- Viable substrate for a fully custom renderer — but we'd hand-build tiling, camera, LOD, labels,
  collision, styling. Only justified if MapLibre + deck.gl both hit walls. **Fallback only.**

### 1.8 New WebGPU-native graph libs (2024–2026 scan)

- **GraphGPU** (graphgpu.com): all-WebGPU pipelines incl. labels; but 29★, force-directed,
  practical limits ~10k nodes/50k edges. Toy scale today. https://github.com/drkameleon/GraphGPU
- **ChartGPU:** WebGPU charting (1M points), not graphs — evidence WebGPU is production-viable in
  2026, not a graph solution. https://github.com/ChartGPU/ChartGPU
- **graphpu:** Rust desktop app, not web-embeddable. https://github.com/latentcat/graphpu
- **Conclusion:** No WebGPU-native graph library is anywhere near production maturity for this
  project. WebGPU arrives for us *through* MapLibre's and deck.gl's backend roadmaps, not through
  a new library bet.

---

## 2. Deep-zoom / tiling precedents

- **MSAGLJS tile pyramids (arXiv 2605.17498)** — the closest published architecture to ADR-0043:
  quadtree tile pyramid over a laid-out graph, importance-ranked (PageRank) node retention per
  level, per-level edge simplification/rerouting, hard per-tile element budget, deck.gl TileLayer
  delivery, cross-fade level transitions, constant per-frame GPU load regardless of graph size.
  Its gap — pyramid built client-side, ~33k node ceiling — is precisely what our server-side
  skeleton/tiler removes. Validates: *the browsing side of the architecture is solved with
  standard map-tile machinery; the hard work is pyramid generation, which we own server-side.*
  https://arxiv.org/html/2605.17498
- **anvaka Map of GitHub / Map of Reddit** — production proof that a similarity-embedded graph of
  ~700k nodes serves beautifully as tippecanoe-generated vector tiles in MapLibre, with labels,
  boundaries, and search. Notably ships *without* visible edges at far zoom (cluster shapes carry
  structure) — matching our "aggregate structure at far zoom" tier.
  https://github.com/anvaka/map-of-github
- **Map of Wikipedia (wiki.halilb.dev, Jan 2026)** — 100k/500k/1M articles, Three.js instanced
  rendering + troika-three-text. Shows 1M nodes is feasible even *without* tiling in a custom
  WebGL app, but its label quality and interaction depth are visibly below MapLibre's.
  https://wiki.halilb.dev/
- **Neuroglancer (Google Connectomics)** — the reference for "billions of elements in a browser":
  multi-threaded client (workers for data/decode), precomputed multi-resolution chunk format on
  static storage, viewport-driven fetch. Volumetric, not graph, but the architectural lessons
  transfer: precompute LOD server-side into a dumb static format; keep the client a streaming
  viewport. https://github.com/google/neuroglancer
- **OpenSeadragon / Deep Zoom** — image pyramids to 2^32 px/side; the pattern (only fetch pixels
  the viewport needs) is the same, but raster tiles of a graph give dead, unstylable,
  uninteractive content; vector tiles strictly dominate for us. https://grokipedia.com/page/deep_zoom
- **Aggregation tooling:** supercluster (Mapbox, hierarchical greedy clustering zoom-by-zoom with
  map/reduce property aggregation → geojson-vt-compatible tiles) and supertiler / clusterbuster
  (server-side cluster tiles, PostGIS variant) are directly reusable *patterns* for our family-
  bubble tier: cluster at max zoom, then re-cluster centroids upward — but we'll cluster by graph
  taxonomy (families), not radius, so this is reference code, not a dependency.
  https://github.com/mapbox/supercluster · https://github.com/ChrisLoer/supertiler ·
  https://github.com/chargetrip/clusterbuster
- **Tile serving:** PMTiles = entire pyramid in one file on object storage, read via HTTP range
  requests; planet OSM ships daily as a single ~107 GB file. This is our zero-ops distribution
  channel for the static bulk of the graph, with a small dynamic tiler only for fresh edits.
  https://docs.protomaps.com/pmtiles/ · https://protomaps.com/

---

## 3. Label rendering at scale

The decisive, underestimated differentiator:

- **MapLibre: native and industrial.** Per-tile symbol placement with global collision index,
  `symbol-sort-key` priority (lower key wins placement), `text-variable-anchor` (high-priority
  labels try alternate anchors before giving up), zoom-dependent reveal, automatic fade
  transitions, `text-allow-overlap`/`text-optional` controls, collision stability under
  pan/zoom/rotate. This is exactly "city names appear as you zoom in" — engineered over a decade
  for world maps. https://maplibre.org/maplibre-style-spec/layers/ ·
  https://github.com/maplibre/maplibre-gl-js/blob/main/src/symbol/placement.ts ·
  https://deepwiki.com/maplibre/maplibre-native/3.3-symbol-placement-and-collision-detection
- **deck.gl: GPU CollisionFilterExtension** — anchor-point-vs-rasterized-area test on GPU, with
  `getCollisionPriority`. Works, but known open issues: label flicker with picking (#9410),
  wrong collisions on icon layers (#8459), no smooth fade semantics like MapLibre's.
  https://deck.gl/docs/api-reference/extensions/collision-filter-extension ·
  https://github.com/visgl/deck.gl/issues/9410 · https://github.com/visgl/deck.gl/issues/8459
- **Sigma.js:** heuristic label grid (density-based selection per frame) — fine for exploration
  tools, below map-grade quality; custom `drawLabel` hooks are canvas-overlay based.
  https://www.sigmajs.org/docs/advanced/customization/
- **Cytoscape.js:** text rendering is a self-acknowledged bottleneck even in the WebGL preview.
  https://blog.js.cytoscape.org/2025/01/13/webgl-preview/
- **Custom (troika-three-text, Canvas2D overlays, GraphGPU):** all punt on collision/priority or
  solve it naively.

**Implication:** choosing MapLibre means label collision, priority, and zoom-reveal — the feature
every graph library fails at — comes free and battle-tested. Choosing anything else means
rebuilding a placement engine.

---

## 4. SSR React framework for the surrounding app

- **Next.js 16** — App Router + RSC mature; Turbopack default; streaming, Partial Prerendering,
  ISR designed for "millions of pages" (per-page regeneration, on-demand revalidation). Self-
  hosting is officially documented; at multi-instance scale the filesystem ISR cache splits per
  pod (documented 30 GB/pod cases) and requires a shared `cacheHandler` (Redis/S3; e.g.
  @neshca/cache-handler) to avoid split-brain staleness. Not Vite (Turbopack). Largest ecosystem
  and by far the densest training-data/agent fluency. https://nextjs.org/docs/app/guides/self-hosting ·
  https://azguards.com/frontend-architecture/the-consistency-gap-unifying-distributed-isr-caching-in-self-hosted-next-js/ ·
  https://github.com/caching-tools/next-shared-cache
- **React Router v7 (Remix lineage)** — production framework mode, Vite-based, clean Node self-
  host, millions of apps. `prerender` config targets build-time lists (unsuitable for millions of
  pages); the scalable path is plain SSR + CDN `stale-while-revalidate` — simple and lock-in-free.
  RSC support is still a **preview** (v7.9.2+, unstable Vite plugin; prerendering not yet
  supported in RSC mode). https://reactrouter.com/how-to/pre-rendering ·
  https://remix.run/blog/rsc-framework-mode-preview
- **TanStack Start** — hit v1 (RC late 2025, stable March 2026). Vite + Nitro (deploy anywhere),
  type-safe routing, TanStack Query first-class, ~30–35% smaller client bundles than Next in
  public benchmarks; full-document SSR + streaming, no RSC complexity. Youngest ecosystem, ~15%
  adoption (Feb 2026 survey), thinnest training-data density.
  https://tanstack.com/blog/announcing-tanstack-start-v1 ·
  https://makerkit.dev/blog/tutorials/tanstack-start-vs-nextjs
- **Millions of crawlable node permalinks — the real answer is framework-agnostic:** never SSG the
  corpus. Render `/node/[id]` on demand (SSR or ISR) from the same graph service, cache at the CDN
  or ISR layer, stream the shell, and hydrate the map client-side. All three frameworks can do
  this; they differ in machinery and ergonomics.

**Recommendation: Next.js**, self-hosted with a Redis-backed cache handler from day one.
Rationale: ISR/on-demand revalidation is purpose-built for the millions-of-permalinks + freshness
pattern; agent fluency (an explicit criterion) is unmatched; self-hosting is a known, documented
path (plus OpenNext as an exit hatch). The graph surface is a client component either way, so the
framework choice is swappable later — the renderer choice is not. **Runner-up:** React Router v7
if we later decide RSC/Next machinery costs more than it returns; its SSR + CDN-cache model is the
simplest correct architecture and fully Vite-native.

---

## 5. Verdict

### Recommended stack

**MapLibre GL JS as the graph surface, fed by our own server-generated vector-tile pyramid
(PMTiles + small dynamic tiler), with deck.gl interleaved via MapboxOverlay reserved as the
escape hatch for near-zoom rich glyphs and morph animations. React (Next.js) orchestrates around
it; sigma.js and everything else are not in the load-bearing path.**

Why this is correct from the start, with no interim engine to replace:

1. **The scaling model is the requirement.** MapLibre + vector tiles is the only candidate whose
   architecture already serves billions of features to a bounded-memory client with smooth
   fractional zoom — proven daily at OSM-planet scale and proven specifically for graph
   embeddings by Map of GitHub. Every graph-native library (sigma, G6, cosmos, cytoscape) would
   need a from-scratch tiling/LOD layer bolted on, and would *still* lack map-grade labels.
2. **Labels come solved** (§3) — collision, priority, zoom reveal, fade. This alone is
   person-years of engineering in any other stack.
3. **The three ADR-0043 tiers map 1:1 to layer types:** far zoom = fill/heatmap/line layers from
   aggregate tiles; mid zoom = symbol+fill "bubble" features with aggregated properties
   (supercluster-style map/reduce); near zoom = circle/symbol layers for nodes (sprite badges,
   data-driven color/dim via feature-state) + line layers for typed edges. Zoom-interpolated
   styles give the continuous transitions.
4. **No dead-end risk:** BSD-3 license, funded independent org, WebGPU backend on the official
   roadmap — the engine modernizes underneath us. Self-hosted tiles (PMTiles on object storage)
   mean zero vendor coupling.

### What we must build regardless of engine (the actual project)

- **Server-side tile generation pipeline:** graph skeleton (in-memory) → per-zoom feature
  selection (importance-ranked, MSAGL-paper-style), family-bubble aggregation with map/reduce
  properties, edge simplification per level, hard per-tile element budgets → MVT encoding →
  nightly PMTiles bulk build + dynamic tiler for recently-edited regions.
- **Layout service:** ELK-class layered layout server-side (Java ELK at scale; elkjs-in-worker
  for local/incremental patches — elkjs exists exactly for worker offload but has no published
  100k-node benchmarks, so budget for the JVM version). https://github.com/kieler/elkjs
- **Layout→Mercator projection discipline:** map layout coordinates into a bounded low-latitude
  Mercator band (distortion grows with |latitude|), define our own zoom↔LOD calibration, and a
  node-ID → (z,x,y) index for permalinks/search flyTo.
- **Bubble collapse/expand semantics** and the bubble→children morph animation (custom layer or
  interleaved deck.gl; no engine provides this).
- **Graph-semantic interactivity** spanning tile boundaries (neighbor highlight, path tracing):
  needs a client-side "visible subgraph" index rebuilt from loaded tile features, or a sidecar
  adjacency fetch per focused node.

### Strongest alternatives (in order)

1. **deck.gl TileLayer + custom layers, standalone** (the MSAGLJS-paper stack): maximum rendering
   freedom, React-first, same server tiler reusable. Costs: rebuild label placement on a less
   mature collision extension; rebuild map polish (fades, inertia tuning). The right move only if
   MapLibre's styling ceiling proves too low — and since it interleaves with MapLibre, it's an
   *augmentation* before it's ever a replacement.
2. **Sigma.js v3/v4 + custom tile loader:** best node-glyph ergonomics; sane if we accepted a
   ≤100k-element world with hand-rolled streaming. Not credible for street-view-over-billions
   without building everything MapLibre already has.
3. **PixiJS v8 fully custom renderer:** total control, WebGPU-ready substrate; last resort with
   the highest build cost and no label engine.

### Biggest risks

1. **Styling ceiling at near zoom (MapLibre):** composite badges/glyphs beyond sprite-atlas
   compositing may force the deck.gl interleaved layer earlier than hoped. Mitigation: prototype
   the near-zoom node style in pure MapLibre expressions + sprites first; the overlay path is
   proven and incremental.
2. **Tile pyramid generation for a *living* graph** is unsolved in the literature at our scale
   (MSAGL paper: client-side, 33k nodes, "per-tile budget enforcement remains an open problem").
   Incremental re-tiling + layout stability over edits is our hardest original engineering.
3. **Coordinate/precision mismatch:** abstract DAG layout in Mercator space at z20+ needs care
   (float precision, distortion band, layout units ↔ zoom calibration). Get the world-coordinate
   contract right before generating the first production pyramid — re-tiling billions later
   because the coordinate system changed would be the classic irreversible mistake.
4. **Bubble morph transitions:** nothing native anywhere; if underestimated, the "street-view
   continuity" feel fails even though rendering succeeds. Prototype early.
5. **Next.js self-host ISR consistency** (split-brain cache) — solved but only if the shared
   cache handler ships from day one.

---

## Source index (primary)

- MapLibre: https://maplibre.org/maplibre-gl-js/docs/ · https://maplibre.org/roadmap/maplibre-gl-js/graphics-modernization/ · https://maplibre.org/maplibre-style-spec/layers/ · https://maplibre.org/news/2026-03-03-maplibre-newsletter-february-2026/
- PMTiles/Protomaps: https://docs.protomaps.com/pmtiles/ · https://protomaps.com/
- Tile-pyramid graph browsing (MSAGLJS): https://arxiv.org/html/2605.17498
- Map of GitHub / Reddit: https://github.com/anvaka/map-of-github · https://github.com/anvaka/map-of-reddit · https://anvaka.org/
- deck.gl: https://deck.gl/docs/api-reference/geo-layers/tile-layer · https://deck.gl/docs/api-reference/extensions/collision-filter-extension · https://deck.gl/docs/developer-guide/webgpu · https://openjsf.org/blog/deckgl-v9
- Sigma.js: https://www.sigmajs.org/ · https://v4.sigmajs.org/ · https://github.com/jacomyal/sigma.js/discussions/1469 · https://www.sigmajs.org/docs/advanced/customization/
- Gephi Lite: https://gephi.wordpress.com/2025/10/08/gephi-lite-v1/ · https://github.com/gephi/gephi-lite
- Cytoscape.js WebGL preview: https://blog.js.cytoscape.org/2025/01/13/webgl-preview/
- cosmos.gl: https://github.com/cosmosgl/graph · https://openjsf.org/blog/introducing-cosmos-gl
- G6 5.x: https://g6.antv.antgroup.com/en/manual/whats-new/feature · https://github.com/antvis/G6
- PixiJS v8: https://pixijs.com/blog/8.16.0 · https://pixijs.com/8.x/guides/components/renderers
- WebGPU graph scan: https://github.com/drkameleon/GraphGPU · https://github.com/ChartGPU/ChartGPU · https://github.com/latentcat/graphpu
- Neuroglancer: https://github.com/google/neuroglancer
- Map of Wikipedia: https://wiki.halilb.dev/
- Clustering: https://github.com/mapbox/supercluster · https://github.com/ChrisLoer/supertiler · https://github.com/chargetrip/clusterbuster
- elkjs: https://github.com/kieler/elkjs
- SSR frameworks: https://nextjs.org/docs/app/guides/self-hosting · https://azguards.com/frontend-architecture/the-consistency-gap-unifying-distributed-isr-caching-in-self-hosted-next-js/ · https://github.com/caching-tools/next-shared-cache · https://remix.run/blog/rsc-framework-mode-preview · https://reactrouter.com/how-to/pre-rendering · https://tanstack.com/blog/announcing-tanstack-start-v1 · https://makerkit.dev/blog/tutorials/tanstack-start-vs-nextjs
