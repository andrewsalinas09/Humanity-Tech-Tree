# Open Questions

Unresolved design debates. Each gets an ID; when settled, mark `Resolved → ADR-XXXX` and write the ADR. Do not silently re-debate these in chat — update this file.

Sources: README brain-dump and the two chat digests in `docs/archive/digests/`.

## Q-01: Logic-group expressiveness vs. simplicity — **Resolved → ADR-0017**
Requirement logic is a boolean expression tree (AND/OR/NOT, arbitrary nesting) on the consumer node, with edge-ID leaves; absent tree = AND of all hard edges. `LogicGroup` and `alternative_path_id` both retired.

## Q-02: Truth-system overlap
Three partially redundant systems accumulated: `ValidityStatus` (on nodes AND edges), `EpistemicStatus` (edges), and a dropped `ConfidenceLevel` for dates (only `uncertainty_range` survived). Define the exact division of labor: scientific validity vs. historiographic confidence vs. edge plausibility.

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

## Q-12: Frontend stack
Cytoscape.js vs. React Flow vs. Qt suggested, none chosen. Blocked-on-nothing until Phase 3 (ADR-0014).

## Q-13: Geometric/interface compatibility
Socket-fits-bracket style constraints (set-intersection logic). Acknowledged as where simulation gives way to abstraction; no mechanism.

## Q-14: Edit wars & disputed causality
DISPUTED states exist in enums, but there is no resolution workflow for "Boolean Logic vs. Vacuum Tubes truly enabled the computer" fights. Related: are person/attribution edges ever mechanical requirements, or pure metadata?

## Q-15: Hairball at full scale / LOD
LOD 0 simulation layer vs. LOD 1 blueprint layer (sim never traverses LOD 1), `is_complete_blueprint`, standard-parts library, "Pantry not Menu" (~2k–50k concept nodes stored, millions of instances only in RAM) — philosophy stated, architecture not committed.

## Q-16: Language/runtime commitment
C++ solver is decided (ADR-0010), but nothing is said about the API server layer between Neo4j/solver and the web, nor build system, nor how the C++ solver is exposed (service? WASM? embedded?).

## Q-17: Storage engine at real scale — decision reopened
ADR-0010's Neo4j choice came from an older-generation LLM conversation and predates the scale estimate (tens of millions–billions of nodes; possibly TBs of data with content/citations). Re-evaluate against the 2026 landscape when Phase 5 approaches (graph DBs, relational+recursive CTEs, columnar, custom). Until then Phase 2 deliberately uses trivially-migratable storage (plain files/SQLite) per ADR-0016 — the *schema/serialization* is the real commitment, not the engine.

## Q-18: Standard/version families and single-node fan-out — **Resolved → ADR-0018**
Family root + significance-gated flat version stars + truth-granular feature attachment with record→edge lifting; fan-out as consumer-edge constraints + capability routers. Validated in `docs/examples/802-11-worked-example.md`. Residual: Phase 2 seed corridor must stress the Microprocessor node at real density.

## Q-19: Authoring UX for high-fan-in nodes (TB-027)
How a contributor adds something like the ASML EUV machine, whose true parents span dozens of domains, without the half-finished node being wrong (it can't be, per ADR-0015 — but it must also not be *useless*). Candidates: domain-sectioned templates, "known-incomplete" badges, LLM-suggested parent checklists, bounties for missing sections.

## Q-20: Semantic existence-search infrastructure (TB-032)
The "does this node already exist?" pipeline at billion-node scale: embed every node at creation, ANN candidate retrieval, LLM same/child/new judgment, stub on uncertainty. Feasibility is not the question (billion-scale ANN is proven); to design: embedding model choice + re-embedding strategy, candidate thresholds, the judgment prompt/criteria, and how the pipeline enforces the create-don't-merge asymmetry (duplicates are incomplete; wrong merges are wrong). This is also the backbone of the ADR-0013 embedding sentinel and the contextual search features — likely one shared service.

## Q-21: EdgeType reduction to the orthogonal basis (TB-038, ADR-0024)
A **reduction** pass, not a collection pass: map every existing enum member and every floated candidate (SIGNIFICANTLY_IMPROVES, ACCELERATES_DEMAND, STIFLES, PROVIDES_RESOURCES, EXPLAINS_PRINCIPLE, CODIFIES, DESCRIBES_METHOD, FUNDED, CONTAINS, ADOPTS, DISCOVERED_USING, APPLIES_TO, FOUNDED, SPUN_OFF_FROM, PRODUCED_BY…) onto the basis per ADR-0024's **partition test** (type ⟺ traversal-pruning need or distinct machine behavior; qualifier otherwise). Straw-man basis (~8): ENABLES / IS_COMPONENT_OF / IS_INGREDIENT_OF / IS_TYPE_OF / IS_REFINEMENT_OF / OPTIMIZES / SUCCEEDS / ASSOCIATION — component-vs-ingredient and type-vs-refinement already ruled IN by the user (DuPont fan-out selectivity), spin-off-flavor ruled OUT (qualifier). Rulings so far (session of 2026-08-09, from the user's Einstein/IEEE-754/flu reasoning):
- **KNOWLEDGE_REQUIREMENT → collapsed into ENABLES.** The time gate is ordinary earliest-possible-date propagation (MAX over dependency dates), which ENABLES runs everywhere; the "humans have no parents except knowledge" insight becomes a linter category rule: BIOLOGICAL_ENTITY nodes only receive ENABLES from knowledge/concepts/works.
- **SPECIFIES_STANDARD → collapsed into ENABLES.** Standards are STANDARD_UNIT nodes; traversers prune on the *target node's category*, so no edge partition is needed (decimals → floats → IEEE 754 is a plain ENABLES chain).
- **Demand/friction are story-layer with signed qualifiers** (drives-need = positive pressure, inhibits/suppression = negative); mitigation (lightning rod) is the demand edge read in reverse, needing no edge (TB-039).

**Last open call (user's):** one story partition or two — split story-causality (INFLUENCES: drives-need, inhibits, precipitated, gave-rise-to, motivated-by, accelerates) from attribution (ASSOCIATION: authored, discovered, founded, custody, brand)? Partition-test argument for two: WWII-scale narrative fan-out where "what did this motivate?" and "who was involved?" are different common queries. Assistant lean: two.

Deliverables: final basis + old→new+qualifier mapping table + per-basis-type category-compatibility rules (isValidConnection linter) + starter qualifier vocabulary + qualifier secondary-index note.
