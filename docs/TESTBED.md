# The Test Bed

The permanent catalog of edge cases. **Every proposed design change must be checked against every case here. Every new edge case gets an entry the moment it's raised — before it's solved.** A schema/mechanism change that breaks any Solved case is rejected or must supersede the relevant ADR.

Statuses: **Solved (design)** — a documented mechanism handles it (cite the ADR/doc); **Partial** — mostly handled, with a named gap; **OPEN** — no accepted answer (should have a Q-ID in OPEN-QUESTIONS).

These are design-time tests today. When code exists, each becomes an executable fixture.

---

## A. Truth, time, and knowledge

### TB-001 — Vacuum-tube iPhone
An iPhone → CPU → switching element → vacuum tube path is technically true. The graph must keep it AND never present it as how iPhones are made.
**Stresses:** technically-true edges, constraint pruning. **Answer:** ADR-0003 (constraints at the seams, e.g. Switching Speed). **Status:** Solved (design).

### TB-002 — Steel/Bessemer bootstrap loop
Iron → tools → steel → Bessemer → better steel. A cycle that must be legal and terminate.
**Stresses:** cycle handling. **Answer:** ADR-0006 (OPTIMIZES edges are existence dead-ends; Temporal Leveling). **Status:** Solved (design).

### TB-003 — Gunpowder is invented twice
One node; China ~850 AD, Europe ~1250 AD; independently "current" in both.
**Stresses:** regional truth. **Answer:** RegionalAvailability with per-region timelines, is_indigenous/import_source. **Status:** Solved (design).

### TB-004 — Roman concrete is lost, then found
Europe: Active (200 BC–476) → Lost (476–1414) → Active (1414–now), with named transition reasons.
**Stresses:** knowledge-status timelines. **Answer:** TimeSegment vector + KnowledgeStatus + transition_reason_slug. **Status:** Solved (design).

### TB-005 — Newton AND Leibniz invent calculus
Independent discovery must not create two Calculus nodes or make either person a dependency.
**Stresses:** people/works layer. **Answer:** ADR-0007 (two Works → one Concept). **Status:** Solved (design).

### TB-006 — GoPro 12 drops GPS; 1–11 and 13+ have it
A feature present, removed, restored across iterations of one product line.
**Stresses:** iteration-level dependency changes. **Answer:** ADR-0009 + ADR-0018 §4 — GPS presence attaches at truth-granularity: iteration-record data for record-only versions, edges to any iteration that has a node, with record→edge lifting. Queryability: iteration records are structured data on the series root, so "which GoPros have GPS?" scans one node's records — acceptable. **Status:** Solved (design).

### TB-007 — Trinity test sorts before Hiroshima
Both 1945; ordering matters for causality rendering.
**Stresses:** date precision. **Answer:** decimal-year DatePoint (1945.54 < 1945.60). **Status:** Solved (design).

### TB-008 — "Bronze Age" vs "July 4, 1776" vs "2 MYA"
Wildly different dating textures with different error bars, all comparable.
**Stresses:** fuzzy time. **Answer:** DatePoint uncertainty_range + TimeScale enum. **Status:** Solved (design).

### TB-009 — "Aliens built the pyramids"
A fringe edge on perfectly valid nodes (Aliens-as-concept, Pyramids) must be storable, filtered by default, and visible on request.
**Stresses:** epistemic filtering. **Answer:** EpistemicStatus on edges; all truth levels stored, view-time filtering. **Status:** Solved (design) — but see Q-02 (truth-system overlap).

### TB-010 — Phlogiston and Miasma
Disproven but historically productive ideas: they motivated real science and inhibited other science.
**Stresses:** wrong-but-influential content. **Answer:** ValidityStatus + BELIEF_SYSTEM nodes + MOTIVATED_BY/INHIBITS/DISPROVED_BY edges. **Status:** Solved (design).

### TB-011 — Leonardo's tank / the Saturn V problem
Designed but never built (THEORETICAL) vs. built but no longer buildable by us (OBSOLETE vs LOST — which is the Saturn V?).
**Stresses:** knowledge-status semantics. **Answer (partial):** KnowledgeStatus enum covers the states; the Saturn V (knowledge exists on paper, industrial base gone) sits awkwardly between OBSOLETE and LOST. **Status:** Partial.

## B. Abstraction, versions, and families

### TB-012 — iPhone 12 vs 13 vs the Wii
Near-identical iterations must NOT get nodes; an iteration with a genuinely new dependency (Wii ← MEMS accelerometer) must.
**Stresses:** node-creation gating. **Answer:** ADR-0009 Significance Filter + ProductIteration records. **Status:** Solved (design).

### TB-013 — One CPU node, hundreds of divergent branches
We refuse per-SKU CPU nodes, yet "CPU" must fan out along many independent axes — speed, size, power, architecture, era — to different consumers with different needs.
**Stresses:** whether attributes + capability edges + refinement chains can carry hundreds of distinct fan-outs from one node without either node explosion or mush. **Answer:** ADR-0018 §7 — diversity lives on consumer edges (constraints), recurring profiles bundle into capability routers, architectures are refinement children; growth is linear + sublinear. Worked in `docs/examples/802-11-worked-example.md` §5. **Status:** Solved (design) — Phase 2 seed corridor must confirm at real density.

### TB-014 — Adding 802.11 TSF
The user rabbit-holes into WiFi and wants to add TSF (Timing Synchronization Function). Where does it go? What about 802.11b/g/n/ax?
**Stresses:** standard families, sub-mechanisms of standards, incremental authoring. **Answer:** ADR-0018, fully worked in `docs/examples/802-11-worked-example.md` — TSF is family-wide since 1997 so it attaches to the root (one node, one edge); version nodes are significance-gated (n ← MIMO, ax ← OFDMA); flat star, not a chain. **Status:** Solved (design).

### TB-015 — Thunderbolt 5 → 4 → 3
A refinement chain where consumers usually care about the family, sometimes about a version (TB3 ← USB-C connector; TB5 ← PAM-3 signaling).
**Stresses:** same as TB-014 from the consumer side: when do existing consumer edges migrate to a new version (re-parenting queue, Q-04)? **Answer:** ADR-0018 §5 — nothing migrates by default (family links stay true); the check queue only *suggests* repointing where the new version is a consumer's more specific truth. TB4 is the filter's proof case: a marketing/certification increment gets an iteration record, not a node. **Status:** Solved (design).

### TB-016 — Betamax
A losing branch that must exist (dead ends are educational) without polluting the winner's lineage.
**Stresses:** divergence handling. **Answer:** Significance Filter rule 5 + SUPERSEDED_BY/REPLACED_BY. **Status:** Solved (design).

### TB-017 — The x86 prototype iPhone
A historical one-off violates the family's requirement ("Mobile Processor"). Reality wins, but the rule must survive.
**Stresses:** exceptions. **Answer:** ADR-0008 widening to LCA + RequirementOverride with justification. **Status:** Solved (design).

### TB-018 — iPhone switches ARM → RISC-V (hypothetical)
A platform transition must not require touching every historical instance.
**Stresses:** dependency inversion. **Answer:** ADR-0008 interface/role nodes created lazily at the divergence moment. **Status:** Solved (design).

## C. Materials, processes, and requirements

### TB-019 — Grease lithium vs battery lithium
One Lithium node; consumers with wildly different purity needs.
**Stresses:** where specs live. **Answer:** ADR-0005 (consumer edge constraints) + ADR-0004 (optimization paths raise purity). **Status:** Solved (design).

### TB-020 — 1kΩ vs 10kΩ resistor (the DigiKey problem)
Millions of SKUs must not become millions of nodes — and per the prime directive, collapsing them must lose no truth, only resolution.
**Stresses:** node-vs-attribute boundary. **Answer:** ADR-0004 Manufacturing Test + Lazy Split. **Status:** Solved (design).

### TB-021 — Platinum OR (Palladium + Heat)
A requirement satisfied by alternatives, one of which is itself a bundle; also "one expert OR a team of ten."
**Stresses:** requirement logic expressiveness. **Answer:** ADR-0017 — boolean expression tree on the consumer node: `OR(platinum, AND(palladium, heat))`; `OR(expert, AND(p1…p10))`. Absent tree = AND of all hard edges; NOT legal but discouraged (monotonicity). **Status:** Solved (design).

### TB-022 — Catalyst vs consumed vs shared
Palladium isn't used up; a factory is shared; lithium is consumed.
**Stresses:** allocation semantics. **Answer:** deliberately deferred with quantities (Q-10). **Status:** OPEN (accepted-open).

### TB-023 — The oil refinery
One process, many outputs (naphtha, kerosene…).
**Stresses:** multi-output processes. **Answer:** pull-based — each product DEPENDS_ON the process node. **Status:** Solved (design).

## D. Editing, growth, and community

### TB-024 — Insert LiIon under Battery
Re-parenting: which of Battery's component edges should move to LiIon?
**Stresses:** the check queue. **Answer:** LLM keep-or-move triage + human review — pipeline unspecified. **Status:** OPEN (Q-04).

### TB-025 — iPhone→Lithium after iPhone→Battery→Lithium exists
A true-but-now-redundant zoomed-out edge must not double-count in BOMs or clutter rendering.
**Stresses:** transitive redundancy. **Answer:** ADR-0021 — `shadowed_by` record on the covered edge; counting queries skip it, truth queries keep it, shadows re-validate when covering edges change; linter proposes, humans confirm, nothing is deleted. **Status:** Solved (design).

### TB-026 — Banana → Nuclear Bomb
Vandalism that is structurally valid.
**Stresses:** semantic sanity. **Answer:** ADR-0013 embedding sentinel + review queues + reputation. **Status:** Solved (design level; parameters open, Q-03).

### TB-027 — The ASML EUV machine has a hundred parents
A contributor adds a node whose true dependencies span optics, plasma physics, precision engineering, software, supply chains. Where do they start, and how does a half-finished node not become *wrong*?
**Stresses:** authoring UX + graceful incompleteness. **Answer (partial):** stub nodes + "incomplete is fine" (prime directive) + templates (ADR-0012); but the actual contributor experience for high-fan-in nodes is undesigned. **Status:** OPEN (Q-19).

### TB-028 — Mid-rabbit-hole authoring
A user three levels deep adds a node whose parents they can't name yet. The graph must accept it and heal later.
**Stresses:** graceful ignorance. **Answer:** stub nodes, magic-box leaves, state re-propagation on fill-in. **Status:** Solved (design).

### TB-029 — WWI ← Franz Ferdinand
The rare case where a person IS the dependency.
**Stresses:** the people-via-works exception boundary. **Answer:** ADR-0007 allows direct links for genuinely person-contingent events; boundary criteria informal. **Status:** Partial.

### TB-030 — The 100th edge case
Someone raises a new scenario in chat and it evaporates.
**Stresses:** the process itself. **Answer:** this file — every new case gets a TB entry before it gets a solution. **Status:** Solved (by construction).

### TB-031 — Tornadoes, wind, and malaria
Technology depends on nature in two directions: as demand (tornado → DRIVES_NEED_FOR → Doppler radar; malaria → quinine) and as hard enabler (wind → windmill; river → water wheel; fault line → geothermal).
**Stresses:** nature as first-class dependency. **Answer (partial):** NATURAL_PHENOMENON category + DRIVES_NEED_FOR and enabling edges cover both directions. **Gap:** natural phenomena need RegionalAvailability too — a windmill is not buildable where there is no wind — and nobody has stated that nature nodes participate in regional buildability logic. **Status:** Partial.

### TB-032 — "Does ASML's parent already exist?" at a billion nodes
A contributor needs a parent node and must learn in seconds whether it exists, under any synonym, among billions of nodes — or duplicates will metastasize.
**Stresses:** semantic existence-search as core infrastructure. **Proposed:** every node embedded at creation; search-first authoring runs ANN candidate retrieval + LLM judgment ("same / child of existing / new"); billion-scale ANN is proven industry tech, so the risk is pipeline design, not feasibility. Prime-directive asymmetry: always err toward creating (duplicates are *incomplete*, fixable by ADR-0011 merge redirects); never auto-merge distinct things (that would be *wrong*). **Status:** OPEN (Q-20).

### TB-033 — WiFi 1–4 lack TSF, 5–8 have it (hypothetical)
Feature presence varying — possibly non-contiguously — across a version family. The GoPro problem (TB-006) wearing a standards hat; one mechanism must solve both.
**Stresses:** version-scoped feature attachment; "graph inside a node" intuition. **Answer:** ADR-0018 §4/§6 — feature presence attaches at truth-granularity (edges to exactly the version nodes that have it; iteration-record data below node granularity; record→edge lifting as a monotone resolution increase). No nested sub-graphs in storage; the family bubble is zoom/LOD rendering. Also closes TB-006's queryability gap. **Status:** Solved (design).

### TB-034 — The iPhone without the feature
Abstract iPhone → Camera / → 802.11 are family truths; iPhone 10 uses 802.11ac while iPhone 18 uses 802.11be; and some instance lacks the feature entirely (real case: no front camera before iPhone 4, 2010; hypothetical: an iPhone with no WiFi). Sibling instances also differ (Sony vs Canon sensor).
**Stresses:** instance-level inheritance, absence of family features, per-instance supplier variation; the NOT-vs-exclusion trap. **Answer:** ADR-0019 — family edges are inheritable defaults; instances WIDEN or EXCLUDE with justification; inherited-unasserted facts render as *presumptions* (incomplete, never wrong); contiguous gaps use dated edges, scattered ones use exclusions; per-instance versions/suppliers were already ADR-0008/0018 (instances link to specific truths). NOT (requires-absence) is documented as the wrong tool for exclusion. **Status:** Solved (design).

### TB-035 — The front camera arrives (retroactive specialization)
"iPhone → Camera" was authored in 2007; in 2010 the front/rear distinction becomes historically important; by 2019 there are ultrawide/telephoto lenses with full specs — but only where contributors care (a dashcam's generic camera edge never specializes).
**Stresses:** role-splitting after the fact; sub-line traits (telephoto = Pro only); opt-in depth for purchase-decision specs. **Answer:** ADR-0020 + `docs/examples/iphone-camera-worked-example.md` — specialization is purely additive (sub-roles via IS_TYPE_OF + edges at truth-granularity, incl. lazy sub-family nodes like iPhone Pro); the still-true generic edge is never archived — it becomes *shadowed* by the covering front/rear edges (ADR-0021), so counts stay correct and zoom-out stays cheap; specs are attributes until the Manufacturing Test says otherwise; uneven resolution is normal and permanent. **Status:** Solved (design).

### TB-036 — Ship of Theseus with a rebrand (Mustang → Mach-E)
A product line where every part lineage is eventually replaced (Mustang gens 1–7), then the brand jumps to something mechanically unrelated (Mach-E, an EV crossover); also pure rebrands with history (Twitter→X), zombie brands (Polaroid), org pivots (Nokia), forks (LibreOffice). "If it can happen in theory the arch needs to handle it gracefully."
**Stresses:** identity over time; the temptation to store a "sameness" judgment. **Answer:** ADR-0022 + `docs/examples/product-morphing-worked-example.md` — identity is the causal chain (never a stored property); dated `name_history`; brands promote to Brand nodes lazily on transplant with dated APPLIES_TO edges (never IS_REFINEMENT_OF across a brand jump); family roots may legally degrade into pure identity containers. All seven mutation types resolve into existing machinery + dated names + one lazy pattern. **Status:** Solved (design).

### TB-037 — Building the Nokia chain from either end
One contributor starts at the paper mill (1865) and works forward; another starts at the phones and works back; a third drops the rubber era in the middle under a different name. All directions and orders must produce the same graph, and browsing must run both ways (paper mill → phones, phones → paper mill).
**Stresses:** bidirectional navigation; insertion-order independence; mid-chain duplicate convergence. **Answer:** ADR-0023 — direction is meaning not access (edges indexed both ways); order-independence is a pinned invariant (already implied by stubs + lazy abstraction + additive specialization + lifting, now a promise no mechanism may break); duplicates from independent starts heal via search-first + merge redirects, so convergence is defined up to merges. Becomes an executable permutation-test fixture once code exists. **Status:** Solved (design).

### TB-038 — Click the newest Keysight scope, reach the HP garage
From one instance node, both lineages must unfold: corporate (scope → Keysight ← spun off from Agilent ← spun off from HP ← founded by Hewlett & Packard, 1939 — with the T&M product line's custody passing across all three orgs) and engineering (scope → ADCs → digital scopes → CRT…), each independently browsable, in either direction, without contaminating each other.
**Stresses:** parallel Did-Happen/Must-Happen layers over one node; corporate spin-offs; product-line custody across org boundaries. **Answer:** composition of ADR-0007 (parallel layers), ADR-0022 (identity is the chain; org churn never touches the dependency tree), ADR-0023 (both directions). Spin-off/founded/custody are NOT new edge types — they are qualifiers on basis edges (ADR-0024): a dated SUCCEEDS edge qualified "spun-off", an ASSOCIATION edge qualified "founded"/"produced-by". **Status:** Solved (design) — final basis names pending the Q-21 reduction.

### TB-039 — Flu, the virus, or the disease: where does demand attach?
Vaccines exist because of influenza. A contributor could hang the demand edge on "flu" (colloquial), the influenza virus (pathogen), or influenza-the-disease. Which is right, and how bad is a misplacement?
**Stresses:** demand-source placement; the demand/ingredient orthogonality. **Answer:** demand attaches to the phenomenon that creates the need — the *disease* (NATURAL_PHENOMENON). The virus separately participates as an ingredient (`virus IS_INGREDIENT_OF vaccine` — attenuated), making this the canonical demo of edge-partition orthogonality: two true edges, two partitions, no overlap. Misplacing demand on the virus is ordinary technically-true-adjacent granularity, healed by refinement + linter (ADR-0003/0020 machinery), never a catastrophe. Bonus ruling (the lightning rod): mitigation needs no edge at all — "rod mitigates lightning" is `Lightning drives-need Rod` read in reverse (ADR-0023); the *inhibits* qualifier is reserved for suppression (Geocentrism vs astronomy). **Status:** Solved (design).

### TB-040 — Could Rome have had steam engines? (the false time-lock)
The counterfactual query must answer "maybe — here are the real gaps (precision boring, pressure-vessel metallurgy)" against Rome's 100 AD regional knowledge state — never "no, because the steam engine depends on an 1800 paper." Works could themselves have been written earlier; only their *inputs* gate possibility.
**Stresses:** counterfactual soundness; contingent vs necessary dependencies; the temptation to anchor tech to dated works. **Answer:** ADR-0025 — two date computations (actual vs earliest-possible); possibility traversal masks out WORK_PUBLICATION and BIOLOGICAL_ENTITY nodes entirely; linter flags ENABLES-from-work ("depend on the concept the work codifies"); person time-bounding (Einstein in 1000 BC) is a Did-Happen-layer validation that never constrains counterfactuals. **Status:** Solved (design).

### TB-041 — The Riemann Hypothesis and the room-temperature superconductor
Conditional knowledge: RH (validity: hypothetical) is a *parent* with hundreds of children — theorems proven assuming it; the scary query is its child subtree ("look what falls if it's false"). A child theorem with an RH-free alternative proof is unconditional. Hypothetical technology: a room-temp superconductor node with 0 parents and a large child tree of not-yet-possible applications built in advance. And the Galois-theory query: which formal concepts have children in distant domains?
**Stresses:** conditionality as entailment; hypothetical leaves; the false-unlock trap; cross-domain bridge queries. **Answer:** all existing machinery — "conditional on RH" is *computed* (does any proof path in the requirement expression avoid hypothetical nodes? — ADR-0017 OR + ADR-0026); "how scary if false" is impact analysis on a conjecture; the unlock cascade is one validity flip. **New rule this case forced:** graceful ignorance's magic-box default (parentless node = REALIZED leaf) applies ONLY to validity=current_truth nodes — hypothetical validity blocks realization regardless of parents, or the parentless superconductor stub would falsely unlock its subtree. **Status:** Solved (design).

### TB-042 — The fallen conjecture: sidestep, salvage, and the missing-node detector
Three math-evolution moves: (a) a new RH-free proof lands — the theorem must instantly become unconditional; (b) the Jacobian Conjecture is disproven, its child subtree collapses, and someone introduces a Weak Jacobian version that salvages most children; (c) the graph says a theorem has no valid support path, but the theorem is independently proven true — the contradiction must be productive, not paradoxical.
**Stresses:** additive proof evolution; conjecture salvage; entailment-vs-fact contradictions. **Answer:** all existing machinery — (a) OR branch to the new proof's *concept inputs* (never the paper, ADR-0025), conditionality recomputes for the whole descendant subtree (ADR-0017/0026); (b) Weak Jacobian is an ordinary new node; "which children survive on the weak form" is a check-queue triage job — the Q-04 pipeline reused verbatim for mathematics; (c) proven-true + no-valid-path = **unrealized**, the same bounty as "iPhone has no path through battery" — the contradiction between entailment and cited fact is an automated missing-node detector that localizes the gap. **Status:** Solved (design).
