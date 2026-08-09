# The Verb Catalog (normative — ADR-0040)

Every write to the graph goes through a verb. A verb is a **deterministic compiler**: `(view, params) → StagedFacts | Decision | Rejection`. Reference implementation: `kernel/httk/verbs.py`; the MCP server and human UI wrap the identical functions (ADR-0029/0040). The LLM never solves — it only resolves Decisions (picking among machine-enumerated legal options) and suggests parameters. Raw node/edge writes are admin god-mode only.

**Result types**
- `StagedFacts` — exact assertions, valid by construction; applied via a ChangeRequest (ADR-0031: breakers at apply, H9 recheck after).
- `Decision(reason, options[], evidence)` — the verb refuses to guess; options are the complete legal set, each with computed evidence. The resolution is provenanced content.
- `Rejection(rule, message)` — deterministic breaker/linter verdict (rule IDs from SCHEMA §11).

---

## Creation

### `propose_node(name, category, validity="current_truth", search_receipt)`
Compiles: `node.create` + validity assertion. **Precondition (computed):** `search_receipt` from a prior `search_similar` call — the existence gate (Q-20) is unskippable by construction. If the gate returned near-duplicates: **Decision** {use existing X (evidence: similarity, category match) | create anyway (justification required) | flag as merge-candidates}. `validity="hypothetical"` is legal (TB-041 guard applies downstream). PHYSICAL-class impossibility claims never enter here — they live on constraints.

### Role-named edge verbs (direction unrepresentable-wrong)
| Verb | Compiles to | Deterministic checks |
|---|---|---|
| `add_component(whole, part, role=None, edge_id?)` | `part —IS_COMPONENT_OF→ whole` | L5 (people are never parts); same-role trigger (below) |
| `add_ingredient(product, ingredient, role=None)` | `ingredient —IS_INGREDIENT_OF→ product` | L5; same-role trigger |
| `add_enabler(enabled, enabler)` | `enabler —ENABLES→ enabled` | L1 (work→concept warn), L2 (people only receive knowledge), L3 (direct person link: justification required + review flag) |
| `classify(instance, type_)` | `instance —IS_TYPE_OF→ type_` | L4 cross-category warn; taxonomy stays a DAG (cycle check) |
| `refine(family, version)` | `version —IS_REFINEMENT_OF→ family` | L4 same-category required; flat-star (ADR-0018): warn if family is itself a version |
| `succeed(old, new, qualifier)` | `old —SUCCEEDS→ new` (dated) | qualifier from vocabulary (canonicalized) |
| `associate(a, b, qualifier)` | `a —ASSOCIATION→ b` | ghost layer; solver-invisible by type |

**Initial conditions (ADR-0042 §3):** every creation verb accepts optional kwargs — `start`, `end`, `epistemic`, `justification` — compiling ONE atomic ChangeRequest, so edges are born complete (the fringe claim born FRINGE; the 2010 camera edge born dated). Anything unstated starts at ZERO, honestly labeled: epistemic absent = "unassessed" (never a mainstream default), validity absent = no standing (solver caps at UNKNOWN), citations absent = red. Justification is never required (except where law demands it: L3, exclusions, L13) but always encouraged.

**Same-role trigger (L11, deterministic):** when a same-type edge into the same consumer exists whose provider shares a taxonomy ancestor with the new provider, `role` is REQUIRED: `"additional"` (joins implicit-AND) or `"alternative": edge_id` (compiles the OR into the consumer's requirement_expr, ADR-0017). Missing → **Decision** {additional | alternative-to-E} with the shared-ancestor evidence. No silent AND, no silent OR.

## Refinement (resolution-increasing, never destructive)

### `intercept(edge_id, via, first_leg_type=None, second_leg_type=None)`
The TB-068 compiler. Compiles: two new edge identities (`from→via`, `via→to`) + `shadowed_by` mark on the original (**shadow, never archive** — the original stays as zoomed-out truth; archive is only for wrong-target edges, via `correct`). Leg types: if omitted → **Decision** listing only category-legal pairs (linter table). If the original edge carries constraints → **Decision** per TB-067: {stay on shadowed edge (still enforced through the chain) | relocate to leg 1 | relocate to leg 2}, seams enumerated. Downstream consumers untouched by construction; H12 keeps expressions whole.

### `specialize(node, sub_roles[])`
The ADR-0020 compiler: creates sub-role nodes (`IS_TYPE_OF` the original) + truth-granular edges; the still-true generic edge is never touched except an optional coverage **Decision**: {mark shadowed by [finer edges] (evidence: coverage analysis) | leave live}. Distinct from `intercept` by construction.

### `exclude(instance, family_edge, justification)`
ADR-0019: stages the EXCLUDE override. Deterministic check: `family_edge` must be inherited via the instance's taxonomy ancestry (computed), else Rejection. NOT ≠ EXCLUDE guard: the verb exists precisely so nobody reaches for expression-NOT.

### `widen(instance, family_edge, to_ancestor=None, justification)`
ADR-0008/H17: legal targets = common ancestors of (original target, exceptional provider), enumerated from the taxonomy DAG. One minimal ancestor → compiled directly. Several incomparable → **Decision** listing them (every option truth-preserving). Param outside the computed set → Rejection.

## Evidence & correction

### `attach_citation(assertion_id, source_node, locator)`
Mechanical. Targets an ASSERTION, never a node (ADR-0038); locator (page/section/anchor) per user ruling. Clears the red badge by computation (ADR-0030).

### `correct(assertion_id, new_value, justification)`
Compiles a superseding assertion (same subject+field, ADR-0011). Identity untouched (ADR-0038: metadata polish stays under the same identity; meaning changes use creation verbs + succession/merge instead).

### `set_constraint(edge_id, attr, op, value, class_="FITNESS", citation=None)`
ADR-0039: `class_="PHYSICAL"` REQUIRES a citation param (L13 — impossibility carries the burden of proof) → Rejection without it. Attr name passes the canonicalization gate (choose-or-mint Decision on near-synonyms).

## Identity surgery

### `merge(src, dst, justification)`
H4 walk to fixpoint at compile time → Rejection on cycle (the Möbius guard, before apply even sees it). Compiles: `migrated_to` + alias/name_history union (H6, mechanical). Iteration records on src → **Decision** per record {append to dst's list | lift into version node V (candidates computed)}. Payloads excluded from scans until triage completes (H6).

### `unmerge(node, justification)`
H5: compiles the forward-edit redirect reversal. Then computes the triage set: assertions recorded AFTER the merge seq touching the canonical — **pre-merge assertions are NOT decisions** (their original homes are computed from record time, H5a — staged automatically); post-merge assertions each become a **Decision** {keep | move | park-at-ancestor (computed; none exists → unplaced-claim bounty)}. Rehomed assertions shed verification events (H5b — computed by the ladder, not by the verb).

## Verification (event verbs — ladder ADR-0032)

`verify_citation(assertion_id)` (agent L2→L3; hardened per H14), `confirm_verification(assertion_id)` (human L3→L4), `vote(assertion_id)` (L5; operator-level independence H16), `challenge(assertion_id, grounds, citation?)`. All append event facts; every level change is computed, never written.

---

## Texture & data verbs (every schema field is authorable — user ruling)

| Verb | Compiles to | Notes |
|---|---|---|
| `set_attribute(node, attr, value)` | attribute declaration (ADR-0004) | name passes the canonicalization gate upstream |
| `add_time_segment(node, region, seg)` | regional timeline segment | ACTIVE/LOST overlap flags the H3 bounty (never rejects) |
| `date_edge(edge, start?, end?)` | edge date assertions | also date params on edge verbs |
| `add_iteration(family, record)` | ProductIteration record (ADR-0009) | duplicate names rejected |
| `lift_iteration(family, name, node_id?)` | **the ADR-0018 §4 lifting operation**: version node + IS_REFINEMENT_OF (dated) + tech edges; record removed | monotone resolution increase |
| `rename(node, new_name, year?)` | name + dated name_history + old-name alias (ADR-0022) | |
| `add_alias(node, alias)` | alias union | |
| `reclassify(node, category, justification)` | category correction — category is a claim, not frozen identity | linter conflicts under the new category are flagged for review |
| `retract_assertion(assertion, justification)` | forward-fact retraction (ADR-0011) | |
| `mark_shadowed(edge, covering[], confirmation)` | human-confirmed L8 resolution (ADR-0021/TB-025) | covering edges must exist; never deletes |
| `add_alternative_bundle(consumer, alternative_to, parts[])` | **the TB-021 shape**: OR branch that is an AND of new edges ("palladium + heat" vs "platinum") | L5 checks per part |
| `move_assertion(assertion, new_subject)` / `park_assertion(assertion, ancestor)` | un-merge triage resolutions (H5) — park flags the H5c bounty | |
| `flag(subject, grounds)` | the bounty entry point (absurd traces, mistakes — the original README gameplay) | |

## The invariant this catalog enforces

**Nothing a caller can express compiles to invalid structure.** Direction lives in verb names; legality lives in computed checks; genuine judgment lives in Decisions whose option sets are machine-complete. A malicious or ignorant caller's worst case is wrong-but-legal *content* — which is exactly what the moderation, verification, and bounty machinery exists to catch.

### `extract_family(parent, siblings, hoist_choice?, justification?)`
The late-arriving taxonomy parent (ADR-0050, TB-071). Parent must exist; ≥2 siblings. Computes claims shared by ALL siblings → Decision ticket with grouped bulk options (`hoist_all` / `hoist_except{exclude:[...]}` / `hoist_only{include:[...]}` / `hoist_none`); resolution compiles to IS_TYPE_OF classifies + family edges on the parent (ADR-0019 inheritable defaults) + `shadowed_by` on covered instance edges. Non-hoisted claims stay at instances. The pick + justification are recorded forever.
