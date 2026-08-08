# Open Questions

Unresolved design debates. Each gets an ID; when settled, mark `Resolved → ADR-XXXX` and write the ADR. Do not silently re-debate these in chat — update this file.

Sources: README brain-dump and the two chat digests in `docs/archive/digests/`.

## Q-01: Logic-group expressiveness vs. simplicity — **the schema conflict to resolve first**
`Node.cpp` carries the three-level `LogicGroup` (functional group AND → variant OR → part AND), but the abstraction chat's final design was a flatter single-level `alternative_path_id` per edge after the user found nested IDs "very confusing." The user's original ask (a group containing "one person" OR "a cluster of 10 people all required") needs two levels; neither shipped design cleanly supports arbitrary nesting. Decide the canonical requirement-logic model before writing the solver.

## Q-02: Truth-system overlap
Three partially redundant systems accumulated: `ValidityStatus` (on nodes AND edges), `EpistemicStatus` (edges), and a dropped `ConfidenceLevel` for dates (only `uncertainty_range` survived). Define the exact division of labor: scientific validity vs. historiographic confidence vs. edge plausibility.

## Q-03: Bot/Sybil defense specifics
Candidates from ADR-0013 (vesting thresholds, embedding sentinel, clique detection) need concrete parameters, and the failure mode of each needs a story. Status: mechanisms named, nothing specified.

## Q-04: Re-parenting check-queue pipeline
When LiIon is inserted under Battery, the parent's component edges enter a queue; an LLM proposes keep-or-move, humans confirm. Unspecified: batch sizes, LLM prompt/criteria, reviewer UX, what happens on disagreement, cost at scale.

## Q-05: Granularity enforcement
Level-skipping (Product → Raw Element) mitigations all remain suggestions: layer model (Substances→Forms→Components→Assemblies→Artifacts), semantic-distance linter, "never link to a parent if a child exists" rule. Also open: assembly-vs-component double counting, method-of-assembly modeling.

## Q-06: Transitive redundancy mechanism
For edges made redundant by refinement (iPhone→Lithium when iPhone→Battery→Lithium exists): shadow/subsumption masking vs. periodic transitive-reduction jobs vs. PRIMARY_REFINEMENT proxy redirects. No single mechanism chosen; probably some combination.

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
