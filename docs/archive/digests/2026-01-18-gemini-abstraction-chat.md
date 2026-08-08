# Digest: Gemini "abstraction" chat (exported 2026-01-18 16:04:43)

Source: `Chats/gemini-conversation-2026-01-18-16-04-43.md` (2,219 lines, read in full).
Topic: how to model abstract vs. concrete things, people, time, and significance. Ends with a consolidated C++ header. Contains NO moderation-layer content (that came from the long chat / README).

## Decisions reached

- **Three-layer abstraction split: Concept (interface) / Paradigm (abstract class) / Artifact (implementation).** If "The Car" and "2024 Toyota Camry" are the same kind of node the graph becomes unusable noise; separating "what it does" from "how it works" from "the historical instance" keeps pathfinding clean (iPhone → Smartphone → WiFi → Frequency Hopping instead of traversing through Nokia 3310).
- **Capability nodes act as routers/buses between physics and engineering.** Without them, `Transistor` would need thousands of direct edges; instead `Transistor → "High-Speed Logic Switching" → Digital Computing → iPhone`. Also makes big jumps legible (Whitworth three-plates → "True Flatness" → gauge blocks → interchangeable parts).
- **Edges flow Provider → Consumer (past → future), "Top-to-Bottom"; all `REQUIRES_*` edge types eliminated in favor of `MAKES_POSSIBLE` etc.** User-imposed rule; single arrow direction makes timeline visualization and traversal unambiguous.
- **People never connect directly to concepts; they connect via WORK_PUBLICATION nodes (Person → AUTHORED → Work → CODIFIES/DESCRIBES_METHOD → Concept).** "wifi needs Hedy Lamarr, but only because she did. Any other person could have done that." Independent discovery handled free (two Works pointing at one Concept). Framed as a **Parallel Graph**: deterministic "Must Happen" engineering tree vs. historical "Did Happen" context layer; validation ignores authorship edges ("A tech is possible when its Physics are met, not when its Author is born").
- **Final logic-group design in THIS chat: `std::optional<int> alternative_path_id` per edge — null = mandatory (AND), same number = same OR-path — plus separate `visual_category_slug` for UI.** Earlier drafts (`discovery_group_id`, `logic_path_id`+`logic_step_id`) were confusing. NOTE: this is FLATTER than the three-level LogicGroup that ended up in Node.cpp — see Q-02 in OPEN-QUESTIONS.
- **EpistemicStatus lives on the *edge*, and ALL truth levels are stored; the user filters at view time.** Valid nodes ("Aliens") can have invalid connections ("Aliens built Pyramids" tagged FRINGE_THEORY alongside the MAINSTREAM_FACT Egyptian path).
- **Time = decimal-year `DatePoint` (negative = BCE) with `uncertainty_range` and `TimeScale` enum; `FuzzyTime` deleted.** Integer years can't order Trinity test (July 1945) before Hiroshima (August 1945); decimal keeps comparison as plain `>`.
- **Knowledge history = vector of `TimeSegment`s with `KnowledgeStatus` (ACTIVE/THEORETICAL/LOST/OBSOLETE/MYTHICAL) + `transition_reason_slug`, nested in `RegionalAvailability`.** The "Roman Concrete Problem": knowledge can be active, lost, and rediscovered per region.
- **Per-region timelines with `is_indigenous`, `import_source`, per-claim citations = the anti-Eurocentrism mechanism.** Gunpowder is one node: China ~850 AD, Europe ~1250 AD. "It's not 2024 everywhere."
- **Product versions are data, not nodes: series root holds `std::vector<ProductIteration>` (name, year, key_feature, optional specific_tech_ids); paradigms carry `minor_examples` text list.** The "Data Explosion" problem: 16 iPhone nodes are noise; create a node only when the object changes dependencies or capabilities of the tree.
- **Six-rule "Significance Filter" for node creation:** 1. Progenitor (first of class), 2. Bridge (cross-domain child), 3. Keystone (deleting breaks a chain), 4. Scale (standardized for humanity, Model T), 5. Divergence (distinct losing branch — Betamax; dead ends are educational), 6. Icon (cultural anchor — Titanic). Worked example: GameCube fails all six (iteration only); Wii passes Divergence (new MEMS-accelerometer dependency) → node.
- **Sibling artifacts (Civic vs. Corolla) attach to the same parent Paradigm but earn nodes via unique inputs** (Civic ← CVCC Engine; Corolla ← TQM). "Share 90% of DNA → same node; fundamentally different goals or lineages → different nodes."
- **Edits are non-destructive: "Split Edge" / `injectNode` archives (never deletes) the old edge when inserting an intermediate node.** Volunteers "don't know what they don't know"; preserves revert against vandalism.
- **Staging layer `ChangeRequest`** (nodes_added, edges_added, edges_removed_ids, vote_count, is_merged): Live Graph + Shadow Graph of proposals reviewers can amend before merging — "Git for History." (Precursor of the README's fuller moderation design.)
- **Distinct TOOL_INSTRUMENT category** (tools used *during* creation but not inside the product) making "tools that make tools" a clean spine. NOTE: later collapsed into TECHNOLOGY in Node.cpp — see long-chat digest.
- **`REQUIRES_KNOWLEDGE` edges as "Time Gate" anachronism check.** "Caveman Bob cannot invent Calculus" — persons need birth/death years; prerequisites must exist within lifetime.
- **REPLACES vs. SUPERSEDES distinct** (old thing stops being used vs. still useful but less accurate); MOTIVATED_BY = predecessor was *wrong* but led to the right path (Chemistry ← Alchemy); ADOPTS = "kept the tools, ditched the magic" (Chemistry ADOPTS Distillation).
- **Default rendering hides context edges ("Ghost Edges"); "History Mode" fades in AUTHORED / ACCELERATES_DEMAND.** Authorship lines are spaghetti and irrelevant to possibility computation.

## Problems raised but NOT resolved

- **Storage/serialization:** SQL "might be painful" for recursive first-principles traversal; JSON/graph structure suggested; never pursued in this chat. (Resolved later in long chat: Neo4j.)
- **Nested logic groups ("group of groups"):** user explicitly wanted two levels (sub-group of one person OR sub-group of 10 people all required); intermediate drafts confusing; final schema flattened to one level — expressiveness vs. UX never squared.
- **Are people/attribution edges mechanical requirements at all?** Gemini hedged; Manhattan Project example waffled between "need every person" and "at least one from cluster." Left ambiguous.
- **Overlapping truth systems:** ValidityStatus (nodes) vs EpistemicStatus (edges) vs a proposed ConfidenceLevel for dates (silently dropped). Division of labor never reconciled.
- **Offered-but-never-written validators:** circular-dependency detector, timeline validator (dependency dates must precede target), `isValidConnection(NodeA, NodeB, EdgeType)` category linter, PersonNode/EventNode payload structs.
- **Early edge-type drafts have semantic inconsistencies:** some illustrated traces use edge types (SIGNIFICANTLY_IMPROVES, ACCELERATES_DEMAND, STIFLES, PROVIDES_RESOURCES, EXPLAINS_PRINCIPLE, CODIFIES, DESCRIBES_METHOD, FUNDED, CONTAINS, ADOPTS) that the final enum doesn't contain.

## Novel ideas/mechanics

- **Compositional / "Reverse Recipe" search** (user's killer feature): search by ingredients (WiFi + Touch Screen + Cellular Radio), intersect used-by sets → Smartphone. Inverted index `component_id → parent_ids` + set intersection. Extends to counterfactuals ("Steam Engine + Gunpowder → Steampunk ironclads").
- **Edge movement costs for A\*:** cheap for abstraction moves, expensive across unrelated paradigms — stops "iPhone → Plastic → Tupperware" routes.
- **Earliest-Possible-Date = MAX(date) over hard dependencies.** "Li-Ion Battery dependency puts a hard lock on the Smartphone timeline until the 1990s." Enables "Can I build a Musket in Europe in 1300?" queries.
- **Environmental edges modify cost/speed, not possibility:** ACCELERATES_DEMAND (WWII → radar), STIFLES, PROVIDES_RESOURCES — a third edge semantics beyond hard deps and optimization. "The Microwave is just a domesticated Radar component."
- **BELIEF_SYSTEM nodes with INHIBITS/DISPROVES** — wrong-but-influential ideas are first-class (Miasma, Geocentrism, Alchemy).
- **`transition_reason_slug`** makes loss/rediscovery queryable ("Fall of Rome", "Library of Alexandria Burned").
- **`impact_weight`, `justification`, `source_urls` per edge; `ResourceCost` + `zoom_level` on nodes.**

## Tech stack discussion

- All schema drafted as C++ structs. No frontend/hosting discussed. DB undecided here (one SQL warning). Wikidata assessed negatively as source of structure: "It has 'Harry Potter' linked to 'England' linked to 'Tea.' It lacks the strict Engineering Hierarchy you are enforcing." A* pathfinding, recursive traversal, boolean unlock evaluator, inverted-index intersection search, `isAvailable(Timeline, year)` scan (ACTIVE + OBSOLETE buildable; LOST + THEORETICAL not).

## Notable quotes

1. "If you treat 'The Car' and 'The 2024 Toyota Camry' as the same *kind* of node, your graph will become unusable (noisy) very quickly."
2. "Your validation algorithm should ignore `AUTHORED` edges when checking for 'Technological Possibility.' A tech is possible when its *Physics* are met, not when its *Author* is born."
3. "If two things share 90% of their DNA (iPhone 12 vs 13), they are the **same node**. If they have fundamentally different goals or distinct engineering lineages (Ferrari vs. Camry), they are **different nodes**."
4. "You are effectively building **'Github for History.'** A version-controlled, dependency-verified graph of human knowledge."
