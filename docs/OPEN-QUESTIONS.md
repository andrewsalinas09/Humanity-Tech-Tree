# Open Questions

Unresolved design debates. Each gets an ID; when settled, mark `Resolved → ADR-XXXX` and write the ADR. Do not silently re-debate these in chat — update this file.

Sources: README brain-dump and the two chat digests in `docs/archive/digests/`.

## Q-01: Logic-group expressiveness vs. simplicity — **Resolved → ADR-0017**
Requirement logic is a boolean expression tree (AND/OR/NOT, arbitrary nesting) on the consumer node, with edge-ID leaves; absent tree = AND of all hard edges. `LogicGroup` and `alternative_path_id` both retired.

## Q-02: Truth-system overlap — **Resolved → ADR-0027**
Two orthogonal axes, kept: validity (content held true today) on nodes AND edges; epistemic (record accuracy confidence) on edges. Date confidence stays numeric; presumption stays derived. The phlogiston case (well-documented AND disproven) is the orthogonality proof.

## Q-03: Bot/Sybil defense specifics
Candidates from ADR-0013 (vesting thresholds, embedding sentinel, clique detection) need concrete parameters, and the failure mode of each needs a story. Status: mechanisms named, nothing specified.

## Q-04: Re-parenting check-queue pipeline
When LiIon is inserted under Battery, the parent's component edges enter a queue; an LLM proposes keep-or-move, humans confirm. Unspecified: batch sizes, LLM prompt/criteria, reviewer UX, what happens on disagreement, cost at scale.

## Q-05: Granularity enforcement
Level-skipping (Product → Raw Element) mitigations all remain suggestions: layer model (Substances→Forms→Components→Assemblies→Artifacts), semantic-distance linter, "never link to a parent if a child exists" rule. Also open: assembly-vs-component double counting, method-of-assembly modeling.

## Q-06: Transitive redundancy mechanism — **Resolved → ADR-0021**
Shadowing: `shadowed_by` records on still-true covered edges, set at edit time / linter-proposed / human-confirmed, re-validated when covering edges change; counting queries skip shadows, truth queries don't. Transitive-reduction jobs become the proposing linter; PRIMARY_REFINEMENT redirects stay separate (migration advice, Q-04 lane). Residual: formal "fully covers" definition per edge type is solver-phase work.

## Q-07: Bulk semantic migration
"Everyone linked Lithium but meant Refined Lithium" — ambiguity flags, consumer-category heuristics, atomic batch repointing, admin god-tools all sketched. Partially defused by fan-in (only ~10-20 core techs touch a raw material directly), but the workflow is undefined.

## Q-08: The Expertise Gap
Who knows the real constraint values (iPhone battery needs 99.9% Li)? LLM co-pilot suggestions, requirement templates (Battery-Grade, Aerospace-Grade), and post-simulation community fact-checking are the candidates. No pipeline defined.

## Q-09: Prototype vs. mass-production scale
When is manufacturing scale a hard requirement (EUV: binary) vs. optional (one-off CNC chassis)? PROTOTYPE_READY/MASS_MARKET_READY tags floated; author wary of encoding scale at all.

## Q-10: Quantities & stoichiometry — **deferred deliberately**
`quantity_ratio` / `AllocationType` (consumed vs. catalyst vs. shared) drafted and explicitly postponed ("I don't think I care about quantities for now"). Capability nodes substitute where quantity is qualitative. Revisit only if simulation needs it.

## Q-11: Data ingestion pipeline
Generator scripts (CSV/Wikipedia lists → 5,000 CPUs), PubChem/SMILES/CAS for chemistry, Wikidata ID linkage — all proposed, none designed. Also: how ingestion respects the Significance Filter (ADR-0009).

## Q-12: Frontend stack — **Resolved → ADR-0044**
The tech tree rendered as a planet: MapLibre GL graph surface over a server-generated vector-tile pyramid (PMTiles + dynamic tiler), deck.gl interleaved for near-zoom richness, Next.js self-hosted with ISR permalinks, React orchestration + Tailwind/shadcn + the trust visual language. Research: `docs/research/2026-08-graph-rendering.md`. Residual frontier: Q-22 (living-graph tiling).

## Q-13: Geometric/interface compatibility
Socket-fits-bracket style constraints (set-intersection logic). Acknowledged as where simulation gives way to abstraction; no mechanism.

## Q-14: Edit wars & disputed causality
DISPUTED states exist in enums, but there is no resolution workflow for "Boolean Logic vs. Vacuum Tubes truly enabled the computer" fights. Related: are person/attribution edges ever mechanical requirements, or pure metadata?

## Q-15: Hairball at full scale / LOD
LOD 0 simulation layer vs. LOD 1 blueprint layer (sim never traverses LOD 1), `is_complete_blueprint`, standard-parts library, "Pantry not Menu" (~2k–50k concept nodes stored, millions of instances only in RAM) — philosophy stated, architecture not committed.

## Q-16: Language/runtime commitment
C++ solver is decided (ADR-0010), but nothing is said about the API server layer between Neo4j/solver and the web, nor build system, nor how the C++ solver is exposed (service? WASM? embedded?).

## Q-17: Storage engine — **Resolved → ADR-0031** (Postgres-first, ratified 2026-08-08)
Research synthesis in `docs/research/2026-08-backend-synthesis.md`; deep-traversal concern addressed in ADR-0031's Traversal Analysis (skeleton-in-RAM + partition-pruned extraction + snapshot analytics); watch list with migration triggers retained. Original framing below for history:

### (historical) Q-17 framing — research ACTIVE (2026-08-08)
ADR-0010's Neo4j choice came from an older-generation LLM conversation and predates both the scale estimate and the agent-first ruling (ADR-0029). Requirements matrix derived from the ADRs — candidates are scored against ALL of these:

- **R1 Scale path:** billions of nodes/edges, TB-scale payloads eventually; but must start tiny and cheap (Phase 2) with a credible growth path — no day-one cluster.
- **R2 Deep traversal:** 10–100-hop recursive dependency chains; fat subgraph extraction for in-memory solving (ADR-0010 pattern); typed-edge partition pruning (ADR-0024).
- **R3 Immutable facts + versions:** full per-entity version history, atomic section rollback, "patient zero" audits (ADR-0011/0026) — append-only/bitemporal models fit naturally.
- **R4 Branching:** shadow-branch ChangeRequests — propose/amend/merge without touching master (ADR-0013); git-like data branching or cheap app-level equivalent.
- **R5 Parallel agent writes:** high-throughput concurrent proposal ingestion with commutative merges (ADR-0023/0029).
- **R6 Semantic search:** embedding per node, billion-scale ANN, integrated or sidecar (Q-20); qualifier/category/validity secondary indexes (R7).
- **R8 MCP-first ergonomics:** cheap machine reads for LLM context assembly; machine-readable diffs and rejection reasons (ADR-0029).
- **R9 Changeability:** self-hostable, sane licensing, and above all a clean export/serialization story — the schema is the commitment, the engine must be swappable (ADR-0016).
- **R10 Dual traversal modes:** actual vs possible with category masks (ADR-0025).

Research streams running: (a) 2026 graph-engine landscape; (b) versioned/branching/bitemporal stores; (c) embedding/ANN + MCP/agent-stack integration. Findings land in `docs/research/`.

## Q-18: Standard/version families and single-node fan-out — **Resolved → ADR-0018**
Family root + significance-gated flat version stars + truth-granular feature attachment with record→edge lifting; fan-out as consumer-edge constraints + capability routers. Validated in `docs/examples/802-11-worked-example.md`. Residual: Phase 2 seed corridor must stress the Microprocessor node at real density.

## Q-19: Authoring UX for high-fan-in nodes (TB-027)
How a contributor adds something like the ASML EUV machine, whose true parents span dozens of domains, without the half-finished node being wrong (it can't be, per ADR-0015 — but it must also not be *useless*). Candidates: domain-sectioned templates, "known-incomplete" badges, LLM-suggested parent checklists, bounties for missing sections.

## Q-20: Semantic existence-search infrastructure (TB-032)
The "does this node already exist?" pipeline at billion-node scale: embed every node at creation, ANN candidate retrieval, LLM same/child/new judgment, stub on uncertainty. Feasibility is not the question (billion-scale ANN is proven); to design: embedding model choice + re-embedding strategy, candidate thresholds, the judgment prompt/criteria, and how the pipeline enforces the create-don't-merge asymmetry (duplicates are incomplete; wrong merges are wrong). This is also the backbone of the ADR-0013 embedding sentinel and the contextual search features — likely one shared service.

## Q-21: EdgeType reduction to the orthogonal basis — **Resolved → ADR-0028**
Final basis (8): ENABLES / IS_COMPONENT_OF / IS_INGREDIENT_OF / IS_TYPE_OF / IS_REFINEMENT_OF / OPTIMIZES / SUCCEEDS / ASSOCIATION, with the full legacy→basis+qualifier migration table in the ADR. One story partition for now (user: "this is a tech tree first and foremost" — story is supporting cast; lazy abstraction applied to the schema itself), with a costless mechanical split-by-qualifier escape hatch if profiling ever demands it. Carried-forward Phase 1 tasks: per-type category-compatibility rules (isValidConnection linter) and the starter qualifier vocabulary.

## Q-22: Living-graph tile generation (ADR-0044 risk #1)
Incremental re-tiling + layout stability for a continuously-edited billion-node graph has NO published solution (the 2026 MSAGLJS paper stops at 33k nodes, client-side; Map of GitHub is a static snapshot). To solve: which tile cells invalidate per fact-append; layout stability under insertion (nodes must not teleport when a neighbor is added — dampened/incremental ELK? reserved-space strategies?); rebuild cadence tiers (dynamic tiler for fresh edits over a periodically rebaked pyramid — the research's proposed split); zoom↔LOD calibration governance (the coordinate contract is frozen SCHEMA-level, ADR-0044 risk #2). We own this frontier.
