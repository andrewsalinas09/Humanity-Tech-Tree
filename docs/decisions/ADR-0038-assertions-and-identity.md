# ADR-0038: Assertions are first-class; identity is separate from assertion — the reference invariant

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** external pre-build review, adopted by user; fixes review points #2 and #3 (one design)

## Context
Two related gaps. (1) Provenance granularity: the prose says citations attach per claim (ADR-0030 §5), but the physical sketch's `citations(claim_kind, claim_id, …)` points at whole nodes/edges — unable to distinguish "iron exists" from "melting point = 1538°C" from "Anatolia had ironworking in 800 BCE." (2) Identity ambiguity: nodes had an identity/version split (`node_id` vs `version_id`) but edges didn't clearly, and `RequirementExpr` leaves, `shadowed_by`, and overrides referenced "edge IDs" without saying whether a correction mints a new ID — risking expressions silently pinning an assertion *version* instead of a semantic relationship. Changing identity granularity after millions of claims exist is the one migration the JSONL escape hatch cannot soften — so this is fixed now.

## Decision
1. **Every ground fact is an assertion with a stable `assertion_id`** — which IS its fact-log `fact_id` (the log was already 80% of the way there). An assertion has subject identity, field/path (predicate), value, and its own record-time lifecycle.
2. **Citations, verification events, challenges, confidence inputs, supersession/retraction, and discreditation all reference assertion IDs** — never bare node/edge IDs. "Cite the node" is no longer expressible; you cite the claim.
3. **Enduring identity is split from assertions about it, for nodes AND edges:** `NodeIdentity` / `EdgeIdentity` (the semantic thing: "copper is a component of this motor") vs the append-only assertions/versions concerning it. A correction supersedes an assertion; the identity endures.
4. **The reference invariant (constitutional):**
   > **References between graph semantics point to identities. Evidence and history point to assertions.**
   Semantics → identities: RequirementExpr leaves, `shadowed_by`, inheritance overrides, taxonomy edges, redirects. Evidence/history → assertions: citations, verifications, challenges, supersession, as-of resolution.
5. **As-of queries compose the two:** identity + record time → the authoritative assertion set at T (ADR-0034 machinery, now with a precise target).

## Why
Assertion-level addressing is what the trust stack (ladder, confidence, demotion cascades, Thera-style competing claims) always assumed — this closes the gap between the prose and the tables. The identity split makes append-only correction safe under every mechanism that holds references: an expression written today means the same *relationship* forever, while the evidence about that relationship evolves underneath it. Joins ADR-0015/0023/0026 as the fourth standing screen: every new mechanism must declare whether each reference it holds is semantic (identity) or evidentiary (assertion).

## Consequences
- SCHEMA §8 revised: `edge_identities` + `edge_assertions` (nodes already split); `citations` and `verification_events` keyed by `assertion_id`.
- SCHEMA §1 carries the invariant; CLAUDE.md rules updated.
- The semantics kernel implements identity resolution + as-of assertion selection as a core primitive.
