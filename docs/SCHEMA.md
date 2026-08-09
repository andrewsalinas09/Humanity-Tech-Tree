# Schema v1 — Phase 1 close-out

**Status: FROZEN v1** (2026-08-08; revised same-day per external review → ADR-0037/0038). **Document authority:** SCHEMA.md, the ADRs, and TESTBED.md are **normative**; ARCHITECTURE.md and README.md are derived summaries — on any conflict, the normative set wins. `Node.cpp`/`AttributeRegistry.h` are historical sketches. Changes here require an ADR and must pass the four constitutional screens — **ADR-0015** (can this ever assert something false?), **ADR-0023** (does the result depend on edit order?), **ADR-0026** (citable fact, or answer the graph should produce?), **ADR-0038** (does each reference point to an identity [semantics] or an assertion [evidence]?) — plus the hardening rules **ADR-0035 H1–H17**, and must break no TESTBED case (67 at freeze).

---

## 1. The model in one paragraph

The store holds only **ground facts** — citable observations, appended forever, never edited or deleted (corrections are new facts). Every fact is an **assertion** with a stable `assertion_id` (= its fact-log line ID): subject identity + field/predicate + value (ADR-0038). Facts describe **nodes** (things), **edges** (relations between things, in an 8-type orthogonal basis), and **events** (submissions, citations, verifications, votes, challenges, merges). Everything else — node state, effective dependencies, earliest-possible dates, verification levels, confidence scores, realizability, conditionality — is an **entailment** computed at query time, **three-valued** (SATISFIED / VIOLATED / UNKNOWN — ADR-0037: absence of evidence never becomes YES), and never stored (caches permitted, never authoritative). **The reference invariant (ADR-0038): references between graph semantics point to *identities*; evidence and history point to *assertions*.** All writes flow through **ChangeRequests** (shadow branches) applied as commutative set-unions; humans and agents author under identical rules; verification is the human-paced bottleneck by design.

## 2. Node

| Field | Type | Governed by |
|---|---|---|
| `id` | UUID | ADR-0001 (instances are first-class nodes) |
| `wikidata_id` | string? | linkage only, never a data source of structure |
| `slug` | string | human-readable key |
| `name` | string | |
| `aliases` | string[] | undated search keys (ADR-0028 search-first) |
| `name_history` | DatedName[] {name, start?, end?} | rebrands; lazy — empty until one happens (ADR-0022) |
| `category` | enum NodeCategory | see §2.1; everything is TECHNOLOGY unless necessary |
| `validity` | enum {current_truth, disproven, superseded, hypothetical, subjective} | ADR-0027 — a fact about mainstream assessment |
| `regional_availability` | RegionalAvailability[] | per-region timelines (§6); nature nodes included (TB-031) |
| `base_attributes` | map AttributeID → variant | ADR-0004; IDs interned via AttributeRegistry |
| `process_output_effects` | modifiers (SET/ADD/MULTIPLY) | ADR-0004 modifier stack |
| `requirement_expr` | RequirementExpr? | §4; absent = AND of all hard edges (ADR-0017) |
| `inheritance_overrides` | InheritanceOverride[] {family_edge_id, WIDEN_TO_LCA\|EXCLUDE, relaxed_target?, justification} | ADR-0019; H7 re-validation; H17 multi-parent |
| `iteration_records` | ProductIteration[] {name, year, key_feature, tech_ids?, exclusions?} | ADR-0009/0018; liftable (ADR-0018 §4, H6) |
| `migrated_to` | node_id? | merge redirect (ADR-0011); acyclic (H4); reversible via Un-merge (H5) |
| `zoom_level`, `wiki_summary`, `image_url` | | display |

**Removed by audit (ADR-0026):** `current_state`, `active_instance_count` — state is computed; the parentless magic-box-REALIZED default applies only when `validity = current_truth` (TB-041 false-unlock guard).

### 2.1 NodeCategory
BIOLOGICAL_ENTITY · ORGANIZATION · GEOPOLITICAL_ENTITY · WORK_PUBLICATION (doubles as source node incl. method sources like calibration curves, H1) · LEGISLATION · HISTORICAL_EVENT · SOCIETAL_ERA · BELIEF_SYSTEM · SOCIETAL_NEED · NATURAL_PHENOMENON (has RegionalAvailability — TB-031) · NATURAL_LAW · FORMAL_CONCEPT · CAPABILITY (router nodes) · MATERIAL · METHOD_TECHNIQUE · STANDARD_UNIT · TECHNOLOGY · BRAND (lazy-promoted, ADR-0022). Categories are the node-side partition key (traversals prune on target category — the IEEE-754 collapse).

### 2.2 Taxonomy is a DAG
IS_TYPE_OF poly-hierarchy is legal (H17). Effective requirements = AND across all taxonomy parents ∪ own edges, same-role requirements deduped by tightening; family roots may legally degrade into identity containers (ADR-0022).

## 3. Edge

| Field | Type | Governed by |
|---|---|---|
| `id` | UUID | edges are first-class |
| `from_node`, `to_node` | node_id | direction = provider → consumer, always; navigable both ways (ADR-0023) |
| `type` | enum (8-type basis, §3.1) | ADR-0024/0028 — the traversal partition key |
| `qualifier` | slug | all flavor (§3.2); machine-invisible; secondary-indexed |
| `truth_level` | enum EpistemicStatus (mainstream_fact → mythology) | ADR-0027 |
| `validity` | enum ValidityStatus | ADR-0027 — disproven mechanisms between valid nodes |
| `start_date`, `end_date` | DatePoint? | multiple active periods = multiple edges |
| `constraints` | AttributeConstraint[] (GT/LT/EQ/CONTAINS) | ADR-0005 — consumer defines the need; evaluation is three-valued (ADR-0037): undeclared attribute or overlapping uncertainty → **UNKNOWN** (never a silent pass, never a block); certain violation → VIOLATED |
| `optimization_factor` | OptimizationFactors? | trade-off deltas |
| `shadowed_by_edge_ids` | edge_id[] | ADR-0021; re-validated on covering-edge change; exempt from implicit-AND (H12) |
| `impact_weight` | float | subjective, labeled as such |
| `justification`, `visual_category_slug` | | provenance/UI |

Citations attach per claim (node, edge, regional entry) as claim→source edges — see §7.

### 3.1 The 8-type basis (ADR-0028; partition test: type ⟺ pruning need or machine behavior)
| Type | Machine semantics |
|---|---|
| ENABLES | existence traversal; ADR-0025 masks (works/people excluded from possibility) |
| IS_COMPONENT_OF | assembled part; BOM counting |
| IS_INGREDIENT_OF | consumed/transformed input |
| IS_TYPE_OF | classification; inheritance flows down (DAG, H17) |
| IS_REFINEMENT_OF | version walks; flat stars under family roots (ADR-0018) |
| OPTIMIZES | existence dead-end; cost/quality traversal; composed-mode rule H10 |
| SUCCEEDS | dated succession story; timeline waves |
| ASSOCIATION | ghost layer; solver-invisible; split-by-qualifier escape hatch |

### 3.2 Starter qualifier vocabulary (grows freely as data; LLM-canonicalized)
- **SUCCEEDS:** replaced · superseded · spun-off · rebranded · forked · merged
- **ASSOCIATION:** authored · discovered · invented · founded · influenced · studied-at · disproved · suppresses · motivated · drives-need · accelerates-demand · precipitated · gave-rise-to · provides-resources · explains · codifies · describes-method · funded · adopted · discovered-using · brand-applies · custody
- Full legacy→basis+qualifier migration table: ADR-0028.

## 4. RequirementExpr (ADR-0017 + hardening)

Boolean tree on the consumer node: leaves = **edge identities** (never assertion IDs — ADR-0038 invariant); AND/OR/NOT, arbitrary nesting; absent = AND of all hard edges. Evaluation is **three-valued with Kleene composition** (ADR-0037): AND — VIOLATED dominates, UNKNOWN dominates SATISFIED; OR — SATISFIED dominates, UNKNOWN dominates VIOLATED; NOT swaps SATISFIED/VIOLATED, UNKNOWN unchanged. Leaves map through inheritance overrides — EXCLUDE prunes its leaf as *vacuous* (removed — distinct from UNKNOWN), all-pruned connectives prune recursively (H11); shadowed edges are exempt from implicit-AND and satisfied by any covering edge (H12); implicit-AND operates over claim-equivalence classes (H13); NOT is legal but discouraged (NOT ≠ EXCLUDE — ADR-0019 §5). Top-level realizability lattice: PROVEN_REALIZABLE / UNKNOWN / PROVEN_UNREALIZABLE, with LOCKED/THEORETICAL/REALIZED as derived UI vocabulary; every result carries its per-claim gap list (the UNKNOWN set).

## 5. Trust & verification (events, all computed downstream)

**Stored event facts:** submission (with provenance: human id / agent pipeline + model + version — ADR-0029), citation attachment, verification run (verifier identity + model + version), human confirmation, vote (reputation-weighted), challenge, retraction/supersession facts on sources (H1), verification-event discreditation (H8), vouch/slash.

**Computed:** the ladder L1–L5 (ADR-0032; L5 = protected-not-frozen; demotion automatic and retroactive), the confidence score 0–100 (§10), the red `[needs citation]` badge (ADR-0030 — empty citations, self-clearing).

**Independence is operator-level** (H16): shared origin collapses identities for L5 counts and the independence term; discovered shared origin voids events retroactively. **Neutrality** (ADR-0036): identical rules for all authors; outcomes computed from evidence only; moderation adjudicates process, never truth.

## 6. Time — three axes, never conflated

1. **Historical time** (domain data): `DatePoint {year: decimal (negative = BCE), uncertainty_range, timescale: GEOLOGICAL|ARCHAEOLOGICAL|HISTORICAL|MYTHOLOGICAL}`. All temporal checks fire only on **certain violation** (disjoint intervals); derived dates propagate by **interval arithmetic** at the coarsest contributing scale (H2). Regional timelines: `TimeSegment {start, end?, knowledge_status: ACTIVE|THEORETICAL|LOST|OBSOLETE|MYTHICAL, transition_reason_slug}`; per-slug evaluation, existential composition, ACTIVE/LOST overlap → region-decomposition bounty (H3). Competing datings = parallel cited claims (Thera pattern).
2. **Possibility time** (entailment): earliest-possible = interval-MAX over necessary deps only; works and people masked (ADR-0025); computed never stored; the counterfactual/debug harness and invention prospector.
3. **Record time** (graph history): every fact carries it; universal as-of queries re-evaluate the full entailment stack with then-current formula/model versions pinned; citable snapshots; diffable citation exports (ADR-0034).

## 7. Sources & citations

Sources are first-class nodes (WORK_PUBLICATION and kin), including **method sources** (calibration curves, dating methodologies — H1, cited per dependent claim). Source reliability is community-assessed *on the source node*. A citation = claim→source edge. Supersession and retraction facts on a source auto-demote every claim citing it (H1 + TB-044).

## 8. Physical schema (Postgres, ADR-0031)

**Ground truth is the fact log** (§9); all tables below are rebuildable projections/indexes over it.

```sql
-- Append-only core (no UPDATE/DELETE on truth columns; supersession by new assertions).
-- ADR-0038 split everywhere: *_identities = enduring semantic things (what references target);
--                             assertions   = dated claims about them (what evidence targets).

node_identities  (node_id, slug, created_by_cr, migrated_to NULL)     -- redirects live on identity
edge_identities  (edge_id, from_node, to_node, type, qualifier, created_by_cr)
                  PARTITION BY LIST (type)                            -- the 8 basis types, physically
assertions       (assertion_id,            -- = fact-log fact_id (stable, citable)
                  subject_kind, subject_id,-- node_identity | edge_identity | source | ...
                  field_path,              -- e.g. base_attributes.melting_point / validity / start_date
                  value JSONB,
                  author, cr_id, recorded_at, superseded_by NULL)
citations        (citation_id, claim_assertion_id, source_node, recorded_at, superseded_by)
verification_events (event_id, claim_assertion_id, kind,             -- l3_run | l4_confirm | vote |
                  actor, model_version, payload JSONB, recorded_at)  -- challenge | discredit | vouch | slash
change_requests  (id, proposer, status, base_snapshot, assertion_ids[],
                  votes, recorded_at, merged_at, merge_log JSONB)    -- the shadow branch (app object)
embeddings       (node_id, model_version, vec vector)                -- pgvector; sidecar jump ~50M (Q-20)
-- Semantic references (RequirementExpr leaves, shadowed_by, overrides, taxonomy, redirects)
--   → identities. Evidence (citations, verifications, supersession, as-of) → assertion_ids.
-- As-of: identity + record time T → the authoritative assertion set at T (ADR-0034/0038).
-- Indexes: edge_identities(from_node), (to_node), (qualifier); assertions(subject_id, field_path);
--          nodes trigram on aliases/name_history; GIN on values; per-partition B-trees.
-- Caches (never authoritative, ADR-0026): dependency_mass, subtree citation-debt counts.
```

**Apply semantics:** CR-apply = transactional commutative set-union of immutable assertions; version forks on the same entity slot are true conflicts → review; circuit breakers run at apply AND re-run post-merge (H9); redirect chains walked to fixpoint at apply (H4).

## 9. The JSONL fact log (canonical serialization; the engine is replaceable, the log is not)

One JSON object per line; append-only; content-hashable for snapshots. Every fact: `fact_id`, `kind`, `recorded_at`, `cr_id`, `author {type: human|agent, id, model?, version?}`, `body`.

```jsonl
{"fact_id":"f_01","kind":"node.assert","recorded_at":"2026-08-08T18:22:03Z","cr_id":"cr_a1","author":{"type":"agent","id":"seed-pipeline-1","model":"claude-fable-5"},"body":{"node_id":"n_tsf","slug":"802-11-tsf","name":"Timing Synchronization Function","category":"METHOD_TECHNIQUE","validity":"current_truth"}}
{"fact_id":"f_02","kind":"edge.assert","recorded_at":"2026-08-08T18:22:04Z","cr_id":"cr_a1","author":{"type":"agent","id":"seed-pipeline-1","model":"claude-fable-5"},"body":{"edge_id":"e_77","from":"n_tsf","to":"n_80211_family","type":"IS_COMPONENT_OF","qualifier":null,"start_date":{"year":1997.0,"uncertainty":0.5,"timescale":"HISTORICAL"}}}
{"fact_id":"f_03","kind":"citation.attach","recorded_at":"2026-08-08T18:25:11Z","cr_id":"cr_a1","author":{"type":"human","id":"andrew"},"body":{"claim":"e_77","source_node":"n_src_ieee80211_1997"}}
{"fact_id":"f_04","kind":"verify.l3","recorded_at":"2026-08-08T18:26:40Z","cr_id":null,"author":{"type":"agent","id":"verifier-fleet","model":"claude-fable-5","verifier_version":"v1.0"},"body":{"claim":"e_77","source_node":"n_src_ieee80211_1997","result":"supports"}}
```

**Snapshot permalinks (ADR-0034):** `htt://snapshot/2031-03-15` (date-based) and `htt://snapshot/sha256-…` (content hash of the log prefix); resolving yields the as-of view; citation exports emit {as-of bundle, current bundle, structured diff}.

## 10. Confidence formula v1 sketch (ADR-0033; code-channel governed, H15)

```
confidence = 100 · squash( Ws·S + Wv·V − Wc·C ), formula_version stamped in every trace
S (sources)      = Σ over independence clusters of reliability(source) with diminishing returns
                   (clusters via shared-origin detection; unassessed sources ≈ small ε)
V (verification) = l3_events (lift CAPPED by cited source's reliability — H14, minus discredited events — H8)
                   + l4_confirms + ratifications (operator-level independence — H16)
C (contest)      = open challenges + superseded/retracted source flags + unresolved disputes
Priors: epistemic enum shifts the squash midpoint (mythology ≫ mainstream_fact).
```
**Golden eval set (mandatory gate for every formula version):** farm-blogs-score-below-independent-gold (TB-061); TB-045 DOS lands mid-band; Thera both-camps stay comparable; hallucinated citation gets ~zero L3 lift (TB-060); L1 uncited = red regardless of author.

## 11. Linter & circuit-breaker table

**Circuit breakers (hard, at CR-apply + post-merge recheck H9):**
| # | Check |
|---|---|
| B1 | Dependency cycle (except through OPTIMIZES) — ADR-0006/0013 |
| B2 | Mass orphaning — ADR-0013 |
| B3 | Embedding-distance anomaly (Banana→Nuclear-Bomb) → freeze for review — ADR-0013 |
| B4 | Redirect acyclicity: `migrated_to` walked to fixpoint; cycle or MERGED target = conflict — H4 |

**Linters (advisory; machine-readable verdicts; route to queues/bounties, never silent rejection):**
| # | Rule | Source |
|---|---|---|
| L1 | ENABLES into the necessary layer *from* WORK_PUBLICATION → "depend on the concept the work codifies" | ADR-0025 |
| L2 | BIOLOGICAL_ENTITY receives ENABLES only from knowledge (NATURAL_LAW, FORMAL_CONCEPT, METHOD_TECHNIQUE, WORK) | ADR-0025 §3 |
| L3 | Direct person→consumer link (non-work): high-friction, justification required, review-flagged (substitutability default 99.9% no) | TB-029 |
| L4 | IS_REFINEMENT_OF across categories → error; IS_TYPE_OF across categories → warn (Q-14 lane) | ADR-0018/H17 |
| L5 | IS_COMPONENT_OF/IS_INGREDIENT_OF from BIOLOGICAL_ENTITY/ORGANIZATION → error (people are never parts) | old-chat validator, formalized |
| L6 | Abstract family root receiving component/ingredient edges when instances exist → suggest attach-to-instance | ADR-0008/0020 |
| L7 | Level-skipping (product → raw element with intermediate children present) → granularity warn | Q-05 heritage |
| L8 | Redundancy radar: transitive coverage detected → propose shadow mark (human-confirmed) | ADR-0021 |
| L9 | Timeline ACTIVE/LOST overlap within a slug → region-decomposition bounty | H3 |
| L10 | Stale override: referenced taxonomy/edges changed → re-validate via check queue | H7 |
| L11 | New second edge filling an existing role → wizard asks "alternative or additional?" (OR vs AND) | ADR-0017 |
| L12 | Uncited claim → red badge (computed; not a linter rejection — never gate) | ADR-0030 |

## 12. MCP surface v1 (ADR-0029; the human UI is a client of the same tools)

`search_similar` (Q-20 existence gate: ANN + judge; create-don't-merge asymmetry) · `propose_node` / `propose_edge` (idempotency keys; typed rejections) · `refine` / `abstract` / `intercept` / `componentize` / `specialize` (wizard verbs; Specialize ≠ Intercept) · `attach_citation` · `verify_citation` (L2→L3, hardened per H14) · `confirm_verification` (L4) · `vote` · `merge` / `unmerge` (H4/H5) · `export_citations(node_set, as_of?)` (ADR-0034) · `get_subgraph(node, depth, masks, as_of?)` — every read returns levels + confidence + traces.

## 13. Implementation checklist (Phase 2 inherits; H-rules as requirements)

0. **Reference semantics kernel + invariant test suite** (before anything user-facing): a small executable library — append facts, as-of/identity/supersession resolution, three-valued RequirementExpr evaluation (ADR-0037), taxonomy inheritance, regional availability, cycle detection — with ~20 of the nastiest TESTBED cases as automated tests. Prose semantics → executable semantics → data; agents implement against the kernel, never against their own reading of this document.
1. Postgres schema + fact-log writer/exporter (§8–9) — with H4 apply-time redirect walk, H9 post-merge recheck.
2. MCP server (§12) with per-agent rate budgets and machine-readable rejections.
3. Existence gate (Q-20 pipeline; embeddings versioned from day one).
4. Ladder + badge computation (ADR-0030/0032, H8, H16); confidence v1 + golden evals (§10, H14/H15).
5. Read-only viewer: rabbit-hole navigation both directions, zoom/LOD family bubbles, red badges, bands+traces, time slider (three axes kept distinct), as-of parameter.
6. Seed content: **the iPhone, all the way up** (user ruling) — organically hits the Microprocessor density test (TB-013 residual) and math conditionality.
7. Solver Phase 4 items explicitly deferred but specified: H2 interval arithmetic, H10 composed mode, H11–H13 expression semantics, ADR-0025 masks.

---

*Everything in this document traces to an ADR (36) and a TESTBED case (64). If a claim here contradicts an ADR, the ADR wins and this document has a bug — file it like one.*
