# Worklog

Append-only session journal, newest entry first. Every agent session ends by adding an entry.

Template:
```
## YYYY-MM-DD — short title
**Done:** what actually changed (files, decisions, code)
**Learned:** anything non-obvious discovered
**Next:** the single most useful next step
```

---

## 2026-08-09 (cont.) — ADR-0023: bidirectional navigation + insertion-order independence (TB-037)
**Done:** User's requirement ("Nokia to paper mill, paper mill to phone, add it anywhere and not be wrong") formalized as ADR-0023: (1) direction is meaning not access — every edge indexed/navigable both ways; (2) insertion-order independence pinned as an invariant — any order of true additions converges to the same graph (already implied by stubs/lazy abstraction/additive specialization/lifting; now a promise no future mechanism may break, and a TESTBED-level acceptance criterion); (3) mid-chain duplicate meets heal via search-first + merge redirects — convergence defined up to merges; (4) becomes an executable permutation-test fixture once code exists. TB-037 Solved. ARCHITECTURE updated.
**Learned:** Order-independence was a lucky consequence of existing decisions; naming it converts it into a design constraint like the prime directive.
**Next:** Q-02 (truth systems), then EdgeType reconciliation (APPLIES_TO and friends waiting).

## 2026-08-09 (cont.) — ADR-0022: identity is the causal chain (TB-036, product morphing)
**Done:** User's exercise: verify the arch survives every way a product can morph, incl. Ship of Theseus + rebrand. Worked example `docs/examples/product-morphing-worked-example.md` (Mustang gens 1-7 → Mach-E brand transplant; Twitter→X; Nokia pivots; Polaroid zombie brand; LibreOffice fork; category drift — 7-type mutation taxonomy, all resolving into existing machinery). ADR-0022 accepted: no stored "sameness" — identity is displayed as the dated causal chain; `name_history` (dated names, lazy) added to Node.cpp; brands promote to Brand nodes only on transplant (dated APPLIES_TO edges; never IS_REFINEMENT_OF across a brand jump); family roots may legally degrade into pure identity containers. TB-036 Solved. Glossary: Brand node, identity container.
**Learned:** The trap was ever answering "is it the same thing?" — any stored sameness flag would eventually be wrong (ADR-0015); chains of dated facts cannot be. APPLIES_TO joins the edge-vocabulary backlog for the EdgeType reconciliation pass.
**Next:** Q-02 (truth systems) — still the last schema-touching open question; edge-enum reconciliation right behind it.

## 2026-08-09 (later) — Q-06 resolved: shadowing (ADR-0021), triggered by "do we break iPhone→camera?"
**Done:** User asked exactly what happens to the generic camera edge. Answer made fully concrete (5-step Specialize operation table; the edge is never broken) and the recurring dependency — the subsumption mechanism — was decided: ADR-0021, `shadowed_by` records on still-true covered edges; edit-time/wizard or linter-proposed + human-confirmed; counting queries skip shadows, truth queries don't; shadows re-validate (and edges resurface) when covering edges change; old transitive-reduction batch job becomes the proposing linter; PRIMARY_REFINEMENT redirects kept separate as migration advice. Node.cpp: `shadowed_by_edge_ids` on DependencyEdge. TB-025 → Solved; TB-035 and camera example updated to cite ADR-0021. Q-06 → Resolved.
**Learned:** Three test cases (TB-025/035 + this question) converged on the same mechanism from different directions — good sign it's the right primitive. Residual solver-phase work: formal per-edge-type "fully covers" definition.
**Next:** Q-02 (truth systems). Phase 1 OPEN list is down to Q-02/03/04/19/20 + deferred Q-10.

## 2026-08-09 (late night) — ADR-0020: additive specialization + uneven resolution (TB-035)
**Done:** User's front-camera edge case (role splits when history makes a distinction important; multi-lens depth only where people care). ADR-0020 accepted: specialization is purely additive — sub-roles via IS_TYPE_OF + edges at truth-granularity; the still-true generic edge is NEVER archived (archiving is only for wrong-target edges); sub-family nodes (iPhone Pro) attach sub-line traits without exclusions; uneven resolution is normal and permanent (depth is opt-in, demand-driven; architecture must permit DigiKey-grade depth, never require it). Worked example: `docs/examples/iphone-camera-worked-example.md`. TB-035 Solved. Q-06 urgency raised (generic+specific coexistence now guaranteed → counting queries need subsumption before Phase 2). Wizard implication recorded: "Specialize" is a distinct additive verb from "Intercept".
**Learned:** The scary-looking reconciliation ("history forces a new distinction") costs two adds and zero edits — the prime directive's payoff in action.
**Next:** Q-02 (truth-systems), and Q-06 moved up the priority list.

## 2026-08-09 (night) — ADR-0019: inheritance + exclusion overrides (TB-034)
**Done:** User's edge case (per-iPhone WiFi versions; an instance lacking a family feature; Sony vs Canon sensors) split into: already-solved (per-instance specificity = ADR-0008/0018) and a real gap — absence. ADR-0019 accepted: family edges are inheritable defaults; instances WIDEN (subsumes ADR-0008's RequirementOverride) or EXCLUDE with justification; inherited-unasserted facts are labeled *presumptions* (keeps ADR-0015 intact); contiguous gaps use dated edges (front camera from 2010), scattered gaps use exclusions. Documented the NOT-vs-EXCLUDE trap (requires-absence ≠ does-not-inherit). Node.cpp: InheritanceOverride struct + field. TB-034 added and Solved. Glossary: exclusion override, presumption.
**Learned:** Real history improved the test case: iPhone 1 HAD a rear camera; the front camera (iPhone 4, 2010) is the true dated-edge example.
**Next:** Q-02 (truth-system overlap) — now four truth-adjacent mechanisms to reconcile (validity, epistemic, date uncertainty, presumption).

## 2026-08-09 (evening) — Q-18 resolved: version families via worked 802.11 example
**Done:** Wrote `docs/examples/802-11-worked-example.md` — full real-history 802.11 walkthrough (family root deps incl. FCC ISM deregulation as LEGISLATION; significance-gated version nodes b/a/g/i/n/ac/ax/be with the new dependency earning each; d/e/h/j as iteration records; TSF attaching to the root since 1997; consumer linking rules; TB-033 counterfactual; Thunderbolt/DDR/CPU-fan-out generalization). ADR-0018 accepted: flat significance-gated version stars (never chained — inheritance stays clean), truth-granular feature attachment, record→edge lifting, no nested sub-graphs in storage (family bubble = zoom rendering), fan-out as consumer-edge constraints + capability routers. TB-006/013/014/015/033 → Solved. Q-18 → Resolved. New glossary terms: family root, lifting.
**Learned:** Thunderbolt 4 is the filter's best proof case — a marketing/certification increment that correctly gets an iteration record, not a node. Misjudged node-worthiness is structurally safe in both directions (create-later + lift, or merge + redirect).
**Next:** Q-02 (truth-system overlap: ValidityStatus vs EpistemicStatus vs date uncertainty), then EdgeType enum reconciliation; Phase 2 seed corridor must include Microprocessor at real density (TB-013 empirical check).

## 2026-08-09 (later still) — Q-01 resolved: requirement logic is a boolean expression tree
**Done:** ADR-0017 accepted (user approved AND/OR/NOT tree, trusting judgment on details): expression tree lives on the consumer node with edge-ID leaves; absent tree = AND of all hard edges; NOT included but editorially discouraged (breaks monotonicity that makes incomplete graphs safe); LogicGroup and alternative_path_id both retired. Node.cpp updated (LogicGroup → RequirementExpr, moved before HistoryNode; edge logic field removed). TB-021 → Solved. Q-01 → Resolved. ARCHITECTURE/GLOSSARY/ROADMAP updated.
**Learned:** The wizard's "alternative or additional?" prompt (ADR-0012 Componentize) is the authoring-side guard that keeps the all-AND default honest.
**Next:** Q-18 — hand-work the full 802.11 family example (versions, TSF, consumers, TB-033 lifting rule) to validate the version-family pattern.

## 2026-08-09 (later) — Nature, semantic existence-search, version-scoped features
**Done:** Added TB-031 (nature as dependency — gap found: natural phenomena need RegionalAvailability for buildability), TB-032 (semantic "does it exist?" search at billion scale → Q-20: embed-on-create + ANN + LLM judgment, create-don't-merge asymmetry), TB-033 (WiFi 1-4/5-8 TSF hypothetical = TB-006 GoPro problem generalized; feature presence attaches at whatever granularity exists, lifts record→edge when version nodes appear). User corrected TB-006 to GoPro 12.
**Learned:** User's "graph inside a node" intuition for 802.11 is right as zoom/LOD *rendering*, rejected as *storage* (would create a second structural mechanism; scoped ordinary nodes/edges + viewer collapse achieve it). User scale ambition confirmed: design must not be limited in theory (billions of nodes).
**Next:** Same as before — work Q-01 (logic model) and Q-18 (version families, now with TB-033) with the user.

## 2026-08-09 — Re-scope: tree before solver; test bed established; prime directive named
**Done:** Created `docs/TESTBED.md` with 30 edge cases (TB-001..030) as the permanent design acceptance suite — including new cases from this session: GoPro GPS gap (TB-006), CPU single-node fan-out (TB-013), 802.11/TSF and Thunderbolt version families (TB-014/015), ASML high-fan-in authoring (TB-027). Wrote ADR-0015 ("never wrong, only incomplete" as the prime directive) and ADR-0016 (tree-first build order — supersedes ADR-0014; solver demoted to Phase 4, community correctness layer promoted to core product). Rewrote ROADMAP accordingly. Added Q-17 (storage engine decision reopened — Neo4j choice came from old-LLM era and predates the TB-scale estimate), Q-18 (version families/fan-out), Q-19 (high-fan-in authoring UX). Wired the test bed into CLAUDE.md rules.
**Learned:** User's framing: the solver was always an added feature — the browsable tree + community correctness (LLM triage + voting, citations) IS the product. Scale ambition: tens of millions–billions of nodes, possibly TBs. Design-on-paper-first is deliberate: schema mistakes at that scale are near-irreversible, hence the test bed as the forcing function.
**Next:** Work TESTBED OPEN cases with the user, starting Q-01 (logic model, TB-021) and Q-18 (802.11/Thunderbolt/CPU worked examples).

## 2026-08-08 — Project restart: documentation system built, old chats distilled
**Done:** Created the full doc system (CLAUDE.md agent contract, docs/: VISION, ARCHITECTURE, GLOSSARY, OPEN-QUESTIONS, ROADMAP, WORKLOG, decisions/ with 14 ADRs, archive/). Digested both Gemini design conversations (~10k lines total) into permanent digests under `docs/archive/digests/` — discovered `Chats/Long chat.pdf` (208 pages) is a print-to-PDF duplicate of `gemini-conversation-2026-01-18-16-05-12.md`, so only the two .md files are canonical sources. Extracted 14 settled decisions into ADRs and 16 open questions into OPEN-QUESTIONS.md.
**Learned:** The old chats settled far more than the README recorded — notably Neo4j + C++ solver split (ADR-0010), state-as-query (ADR-0002), the Manufacturing Test / Lazy Split rules (ADR-0004), the Significance Filter (ADR-0009), and the tracer-bullet build order (ADR-0014). One genuine schema conflict surfaced: Node.cpp's three-level LogicGroup vs. the chat's flatter `alternative_path_id` design (Q-01) — this blocks the solver and should be resolved first.
**Next:** Resolve Q-01 (requirement-logic model), then start Phase 1 tracer bullet (ROADMAP).
