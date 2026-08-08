# Architecture (current state)

The living description of the design as it stands. `Node.cpp` / `AttributeRegistry.h` are the source of truth for exact fields; this doc explains the *systems*. Rationale lives in `docs/decisions/`; unresolved items in `docs/OPEN-QUESTIONS.md`.

## 1. The graph

Two simultaneous structures, both made of edges:
- the **dependency graph** (horizontal, causal: MAKES_POSSIBLE / IS_COMPONENT_OF / IS_INGREDIENT_OF / OPTIMIZES…)
- the **taxonomy tree** (vertical: IS_TYPE_OF / IS_REFINEMENT_OF)

Edges flow **provider → consumer** (past → future), never `REQUIRES_*` — one arrow direction keeps traversal and timeline rendering unambiguous.

### Abstraction layers
Concept ("Car", the interface) / Paradigm ("Internal Combustion Automobile", the abstract class) / Artifact ("Benz Patent-Motorwagen", the instance). **Capability nodes** ("High-Speed Logic Switching", "True Flatness") act as routers between physics and engineering so Transistor doesn't need edges to every gadget ever built.

Abstraction is **lazy** (ADR-0008): link to the most specific true leaf; create interface/role nodes ("Mobile Processor") only when a second real implementation forces it. Historical exceptions *widen* requirements to the Least Common Ancestor (recorded as RequirementOverrides) rather than deleting them.

Node creation is gated by the six-rule **Significance Filter** (ADR-0009); minor versions live as `ProductIteration` data inside a series-root node, not as nodes.

### Nodes (`HistoryNode`)
- **Identity:** UUID, optional `wikidata_id`, `slug`, `name` + `aliases` (aliases power search-first dedup).
- **Category** (`NodeCategory`): biological entity → … → technology. TOOL/COMPONENT/ARTIFACT are deliberately collapsed into TECHNOLOGY — "everything is a technology unless absolutely necessary."
- **State:** LOCKED / THEORETICAL / REALIZED is **computed** from (Time + Location + Node) — ADR-0002. The struct's `current_state` is a vestigial cache for abstract-node realization only.
- **Regional availability:** per-region `Timeline` of `TimeSegment`s (KnowledgeStatus: active/theoretical/lost/obsolete/mythical + `transition_reason_slug`), `is_indigenous`, `import_source`, per-claim citations. Models lost knowledge (Roman concrete) and multi-origin tech (gunpowder); the anti-Eurocentrism mechanism.
- **Attributes:** `base_attributes` (AttributeID → variant value, interned via `AttributeRegistry`); process nodes carry `AttributeModifier`s (SET/ADD/MULTIPLY). See §3.

### Edges (`DependencyEdge`)
First-class, with own identity and metadata:
- **Truth:** `EpistemicStatus` (mainstream fact → mythology) and `ValidityStatus`, independent axes; ALL truth levels are stored, users filter at view time. (Overlap between the truth systems is unresolved — Q-02.)
- **Time:** optional start/end `DatePoint` (decimal year, negative = BCE, `uncertainty_range`, `TimeScale`). Multiple active periods = multiple edges. Decimal years exist so Trinity (1945.54) sorts before Hiroshima (1945.60).
- **Requirement logic:** ⚠️ two competing designs — three-level `LogicGroup` (in code) vs. flat `alternative_path_id` (chat's final word). **Q-01, resolve before the solver.**
- **Constraints:** `AttributeConstraint`s (GT/LT/EQ/CONTAINS) — always declared by the consumer (ADR-0005).
- **Optimization factors:** per-edge deltas (cost, rate, quality, size, energy, safety, accessibility; negatives = trade-offs).
- **Provenance:** `justification`, `source_urls`, `impact_weight`, `visual_category_slug` (pure UI grouping).

## 2. Solver semantics

- **Existence traversal skips OPTIMIZES edges** — the cycle-breaker that makes bootstrap loops legal (ADR-0006). Cost/quality queries traverse them. Improvement loops resolve generationally ("Temporal Leveling": Gen-0 output builds the optimizer that upgrades Gen-1).
- **Constraint pruning** (ADR-0003): technically-true paths (vacuum-tube computer) are pruned by attribute constraints at the seams (Switching Speed), not by manual bans. Gatekeeper nodes (Integrated Circuit) encode era boundaries topologically. If every path dies, the node is *unrealized* → public bounty.
- **Modifier Stack** (ADR-0004): the solver composes virtual material instances (base attributes + stacked optimizer processes) and checks them against consumer constraints. New refinement tech is picked up automatically.
- **Requirement inheritance:** refinement children inherit and tighten parent requirement edges at solve time (`getRecursiveRequirements` merge).
- **Graceful ignorance:** dependency-less nodes are magic-box REALIZED leaves; unknown IDs become STUB nodes; filling gaps later re-propagates state. The graph must tolerate being incomplete everywhere, always.
- **Diagnostics:** LCA analysis explains invalid connections and offers quick-fixes (swap / reclassify / widen). Impact analysis (kill-a-node) shows downstream collapse vs. multi-path survivors.

## 3. Storage & runtime (ADR-0010)

Neo4j stores the graph and serves fat subgraph queries; a C++ engine owns all decision logic (constraints, modifiers, overrides, cycle detection, temporal validation) over the in-memory subgraph. Attribute maps serialize as JSON properties. `AttributeRegistry` interns attribute names to uint32 IDs (thread-safe singleton). API/server layer between them: undecided (Q-16). Phase 1 skips Neo4j entirely (ADR-0014).

## 4. The human layer

People connect via WORK_PUBLICATION nodes (ADR-0007); possibility checks ignore authorship. `KNOWLEDGE_REQUIREMENT` edges gate anachronisms (a person cannot predate their prerequisite knowledge). Narrative edges (PRECIPITATED, GAVE_RISE_TO, INHIBITS, MOTIVATED_BY…) and belief systems capture the "Did Happen" story; default rendering hides them, History Mode fades them in.

## 5. Editing, versioning, moderation

- **Nothing is deleted** (ADR-0011): merge redirects, deprecation lifecycle, archived edges; `version_uuid`/`previous_version_id`/author/timestamp on every entity from day one → atomic rollbacks, vandalism audits.
- **Contributors get verbs, not edge-drawing** (ADR-0012): Refine / Abstract / Intercept / Componentize + templates; search-first creation.
- **Four-layer moderation** (ADR-0013): blast-radius permissions by `dependency_mass`, shadow-branch ChangeRequests, circuit breakers (cycle check, orphan check, embedding sentinel), vouch-based trust chain with reputation at stake. Bot defense: vesting, anomaly clusters, Sybil clique detection.
- **Re-parenting check queue:** inserting an instance under an abstract node queues the parent's component edges for LLM keep-or-move triage + human confirmation (pipeline unspecified — Q-04).

## 6. Signature queries (what the system must be able to answer)

- First-principles derivation: full dependency chain of X down to natural law.
- "Can I build a Musket in Europe in 1300?" — earliest-possible-date = MAX over hard deps, intersected with regional timelines.
- Compositional "reverse recipe" search: {WiFi, Touchscreen, Cellular} → Smartphone (inverted index + intersection).
- Impact analysis: kill a node, watch dependents die.
- "How was X first made" (skip optimizers) vs. "how is X made well" (traverse them).
