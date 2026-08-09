# ADR-0040: Verbs are deterministic compilers; the LLM is never in the transaction

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user directive ("I want things to be solved rather than LLM-based — the LLM is there for ambiguity, not solving. I don't want humans OR LLMs to break anything with ignorance")

## Context
The edit verbs (ADR-0012/0020, H5/H6) were named but hand-wavy: no operational semantics, and an implicit reliance on "the LLM figures it out" — which at swarm scale means nondeterministic, unauditable, ignorance-breakable writes.

## Decision
1. **Every verb is a total, deterministic compiler:** `(view, params) → StagedFacts | Decision | Rejection`.
   - **StagedFacts** — the exact assertion list, valid by construction; applying it is mechanical (backend CR apply, ADR-0031 breakers included).
   - **Decision** — where a genuine choice exists, the verb REFUSES TO GUESS: it returns the machine-enumerated set of *legal* options plus the computed evidence for each. The caller picks; the pick is recorded with provenance and is ordinary reviewable content.
   - **Rejection** — a deterministic breaker/linter verdict with a machine-readable rule ID.
2. **Illegal structure is unrepresentable at the public surface.** No raw `create_edge(from,to,type)` for humans or agents — only role-named verbs whose signatures encode direction and shape (`add_component(whole, part)`, `add_ingredient(product, ingredient)`, `add_enabler(enabled, enabler)`, `classify(instance, type_)`, `refine(family, version)`, `succeed(old, new, qualifier)`, `associate(a, b, qualifier)`, `intercept`, `specialize`, `exclude`, `widen`, `merge`, `unmerge`, `attach_citation`, `correct`, `set_constraint`). Raw edge/node writes are admin god-mode, logged as such.
3. **All validation is computed, never asked:** category-compatibility (linter table), breaker walks (H4/B1), coverage checks, common-ancestor enumeration (H17), same-role candidate detection, pre-merge-home computation (H5a) — every one is a deterministic function of the current view.
4. **The LLM's entire legal role:** (a) resolving Decisions — choosing among enumerated options; (b) suggesting — pre-filling parameters, drafting justifications, proposing which verb to use. Both outside the transaction; both land as provenanced facts. An LLM (or human) can choose wrong-but-legal (reviewable content, the moderation lane); it structurally cannot produce invalid graph.
5. **One surface (ADR-0029 sharpened):** the MCP tools and the human UI invoke the identical verb functions; a Decision renders as a dialog (human) or a typed option list (agent). No capability exists in one skin and not the other.
6. **Known ambiguity points, all Decision-typed:** alternative-vs-additional (L11 — triggered deterministically when a same-type edge exists whose provider shares a taxonomy ancestor with the new provider); interposition leg types (only category-legal pairs offered); constraint relocation on intercept (TB-067 — stay / seam options enumerated from the chain); widen target among incomparable ancestors (H17); coverage confirmation for shadowing (ADR-0021); un-merge triage of post-merge assertions (H5 — pre-merge assertions are NOT decisions: their homes are computed from record time).

## Why
Determinism is what makes the swarm safe: a million agents calling compilers produce auditable, replayable, order-independent facts; a million agents "figuring it out" produce drift. Enumerated-choice is the correct division of labor — machines are complete (they list every legal option), LLMs/humans are judicious (they pick well) — and it caps the blast radius of bad judgment at "reviewable content," never "broken structure." This is ADR-0026's spirit applied to writes: the verb computes everything computable; only genuine judgment is delegated.

## Consequences
- `docs/VERBS.md` (normative, alongside SCHEMA.md) specifies every verb: signature, computed preconditions, compiled facts, decision points with their enumeration rules.
- `kernel/httk/verbs.py` implements the compilers as the executable reference; MCP server (step 2) wraps them 1:1.
- The check-queue pipeline (Q-04) is recast: queue items ARE Decisions; the LLM triages by picking options, humans confirm — nobody free-writes.
