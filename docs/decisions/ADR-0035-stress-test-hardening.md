# ADR-0035: Stress-test hardening — 17 rules from the 2026-08-08 red-team

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** adversarial stress test (7 attack dimensions, 26 distinct findings, skeptic-verified; report: `docs/research/2026-08-stress-test-report.md`). Verdicts: **0 BREAKS, 17 PARTIAL, 9 HANDLED**. Every PARTIAL's missing rule is codified here; each is an amendment to a named ADR, not new machinery.

## Preamble clarifications the verification pass produced
- **ADR-0026 scope:** the store tracks *what sources assert* — measured/calibrated values cited to papers are legal ground facts ("paper P dates this stratum to 6200 BC"). The stored-inference ban targets the graph's OWN derived values. Being behind a moving literature is incompleteness, not wrongness.
- **ADR-0033 formula governance:** the confidence formula lives in the CODE channel (versioned, eval-gated, revert-visible), not the community edit surface — there is deliberately no vote-a-formula-in mechanism to capture.

## The rules (H1–H17)

**H1 — Method-source citations + supersession demotion** *(amends ADR-0032; TB-047).* Method sources (calibration curves like IntCal, dating methodologies) are WORK_PUBLICATION source nodes cited per dependent claim (authoring/ingestion convention). ADR-0032's automatic-demotion event set extends from *retraction* to **supersession** facts on source nodes — a superseded curve demotes confidence on every claim citing it, feeding the standing repair-bounty machinery.

**H2 — Interval temporal semantics** *(amends ADR-0025/TB-007; TB-048).* All temporal consistency checks fire only on **certain violation** (intervals disjoint in the violating direction; overlap passes — incompleteness, never a false flag). Derived dates (MAX over deps) propagate via **interval arithmetic**, results carrying the coarsest contributing TimeScale, never a bare scalar. TB-042's contradiction detector consumes only certain violations.

**H3 — Timeline coherence** *(amends ADR-0002 evaluation; TB-049).* State queries evaluate against exactly one region slug (never inferred containment). Within a slug, overlapping segments compose existentially: ACTIVE satisfies buildability; LOST blocks only where no ACTIVE covers the instant. An ACTIVE/LOST overlap flags a region-decomposition bounty (TB-045 applied to geography). CR conflict granularity for timelines pins to field level.

**H4 — Redirect acyclicity is the fourth circuit breaker** *(amends ADR-0013; TB-050).* CR-apply setting `migrated_to` walks the target's redirect chain to fixpoint; reaching the source (or any MERGED target) is a true conflict routed to review. Redirect resolution is defined as follow-to-fixpoint with cycle detection surfacing a repair bounty.

**H5 — The Un-merge verb exists** *(amends ADR-0011/0012; TB-051; extended per user 2026-08-08).* Un-merge = forward-edit reversal of the redirect reopening the merged node + triage of assertions (the Q-04 LLM-proposes/human-confirms shape), with:
- **H5a — merge history is the triage prior:** pre-merge assertions' original homes are in the record-time history, so their keep/move is mechanical; only record-time-post-merge assertions need real judgment.
- **H5b — verification reset and re-climb:** an assertion rehomed by un-merge (or any surgery that changes the claim's subject) keeps its citation facts but NOT its verification events — the events attached to the old claim. The computed level lands back at ~L2, machine verification re-lifts to L3, and the bounty game re-climbs to L4/L5. (Follows from ADR-0032's computed ladder; stated here so nobody "preserves" stale L5 on a changed claim.)
- **H5c — parking generalized:** park at any common ancestor (minimal preferred; among incomparable minimal ancestors the choice is editorial, per H17). If NO common ancestor exists — itself diagnostic of a maximally-wrong merge — the rare ambiguous assertion parks as an **unplaced claim** attached to the un-merge event: a standing bounty on no node. Never force an assertion into a possibly-false home.

**H6 — Merge payload semantics** *(amends ADR-0011; TB-052).* On MIGRATED_TO: aliases/name_history union onto the canonical node; each non-canonical iteration record enters triage (Q-04 shape) — append to canonical list or lift (ADR-0018) into an existing version node; conflicts land as ordinary contested facts; until processed, MERGED-node payloads are excluded from scans.

**H7 — Override records re-validate on surgery** *(amends ADR-0008/0019; TB-053).* Like shadows (ADR-0021 §4), RequirementOverride/widening records re-validate when the taxonomy or edges they reference change (insertion of a finer ancestor, re-parenting); invalidated overrides enter the check queue rather than silently pinning stale shapes.

**H8 — Verification-event discreditation fact type** *(amends ADR-0032; TB-054).* A citable appended fact (scope: verifier model+version or pipeline identity, optional record-time window, source: the audit) that the level function and confidence formula exclude matching verification events on — exactly parallel to source-retraction facts. Instant graph-wide demotion, re-verification queues, as-of reproducibility all follow from existing machinery.

**H9 — Post-merge breaker recheck** *(amends ADR-0013/0031; TB-055).* Structural circuit breakers (cycle, orphan) re-run against post-merge master — as a serialized recheck inside the transactional apply and/or in the periodic skeleton-snapshot analytics — routing *jointly*-violating CR pairs to review as a flagged pair (flags, never reorders; merge commutativity preserved).

**H10 — Composed-mode solver evaluation** *(amends ADR-0006; TB-056).* A Modifier-Stack invocation inside an existence solve is itself a realization check of the optimizer process at the query's (time, place), evaluated generation-indexed: generation g may use only attribute states achievable at g−1, with the OPTIMIZES-skip applying inside the re-entered subgraph; termination by Temporal Leveling's monotone fixpoint.

**H11 — RequirementExpr × exclusion** *(amends ADR-0017/0019; TB-057).* Instances inherit the family RequirementExpr with leaves mapped through the override set: an EXCLUDE prunes its leaf; a connective whose children are all pruned is pruned recursively (vacuous — neither TRUE nor FALSE); surviving inherited structure carries presumption status.

**H12 — Shadowed edges are exempt from implicit-AND** *(amends ADR-0017/0021; TB-058).* An edge appearing in another edge's `shadowed_by` never joins the implicit-AND set; a leaf referencing a shadowed edge is satisfied by that edge OR any covering edge.

**H13 — Implicit-AND over claim-equivalence classes** *(amends ADR-0017; TB-059).* Requirement evaluation operates over claim-equivalence classes: an edge duplicating (or shadowed by) an edge already represented in the expression is excluded from implicit-AND — implicit-AND applies only to edges carrying claims not already represented.

**H14 — L3 verifier hardening + reliability-capped lift** *(amends ADR-0032/0033; TB-060).* The L3 machine verifier treats fetched source content as untrusted DATA (injection-hardened, instruction-stripped). L3 lift in the confidence formula is capped by the cited source node's assessed reliability — near-zero lift from un-assessed self-hosted sources.

**H15 — Formula governance stated** *(amends ADR-0033; TB-061).* Formula versions change only through the code channel: golden-claim eval gate mandatory (the "5 blogs quoting each other must score differently" behavior is a preserved requirement, not taste), version visible in every trace, reverts diffable via as-of.

**H16 — Independence is operator-level** *(amends ADR-0032 §L5, ADR-0013; TB-062).* Independence for confirmations/votes is defined at operator/origin level: identities sharing declared or detected origin (operator, funding, hosting, model+prompt provenance) collapse to one for the L5 count and the independence term. Undeclared shared origin discovered later voids the affected events retroactively (automatic demotion).

**H17 — Poly-hierarchy composition** *(amends ADR-0008/0019; ARCHITECTURE "taxonomy tree"→DAG; TB-063).* IS_TYPE_OF poly-hierarchy is legal (taxonomy is a DAG). Effective requirements compose across ALL taxonomy parents as the AND of each parent's inherited expression ∪ own edges, same-role requirements at different granularity deduped by tightening when IS_TYPE_OF-related. WIDEN targets *any common ancestor* of original target and exceptional provider; choice among incomparable minimal ancestors is editorial content (Q-14 lane) — safe because every choice is truth-preserving.

## Why one omnibus ADR
Each rule is a one-paragraph amendment forced by existing principles; scattering 17 micro-ADRs would bury the red-team's provenance. Each amended ADR remains authoritative for everything else; on conflict, this ADR wins as the later ruling.

## Consequences
- TESTBED gains TB-047..TB-063 (section G). ARCHITECTURE taxonomy wording fixed to DAG.
- Phase 2/4 implementation checklists inherit H-rules as requirements.
- The 9 HANDLED findings are recorded in the report as validated defenses (free proofs).
