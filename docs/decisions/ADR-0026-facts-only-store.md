# ADR-0026: The store holds only ground facts; everything else is entailment

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user hard-lock, restart session 2 ("ONLY write down facts... we write down things, and then we solve what results from it")

## Context
Three decisions had independently arrived at "derived, never stored": node state (ADR-0002), effective dependencies (ADR-0019), earliest-possible dates (ADR-0025). Each was a local instance of one axiom that had never been stated globally.

## Decision
1. **The store is a fact base.** Every stored datum is a *ground fact*: an observation about the world, in principle citable to a source. "The iPhone was released in 2007" — fact, store it. "Could Bill Gates have built the iPhone?" — not a fact about the world but a consequence of facts (what he knew, what the iPhone requires); the solver answers it, nothing stores it.
2. **Everything modal, hypothetical, or aggregate is an entailment** — computed fresh from the fact base at query time: possibility, earliest-possible dates, node state, effective dependency sets, unrealized status, impact analyses, counterfactuals. (Formally: the extensional/intensional split — the store is the EDB, the solver defines the IDB.)
3. **The schema litmus test** for any proposed field: *"Could someone cite a source for this value, or is it an answer the graph should produce?"* Answers must never become fields. This screen applies to every future schema change alongside the prime directive (ADR-0015) and order-independence (ADR-0023).
4. **Caches are performance artifacts, never authorities.** Derived values may be cached (`dependency_mass`, abstract-node realization counts) but must always be recomputable from ground facts, and recomputation always wins a disagreement. A cache that can win is illegal stored inference.
5. Subjective editorial data (impact_weight, significance judgments, qualifiers) is still fact — facts about *human assessment*, labeled as such (ADR-0015 §consequences) — not entailment.

## Why
Stored inferences go stale the moment any contributing fact changes, and at billions of nodes nobody can find which ones — stored inference is future wrong information (prime directive violation by time bomb). Entailments computed from the current fact base are always exactly as good as the facts, improve automatically as the graph fills in, and make the counterfactual debug harness (ADR-0025 §6) trustworthy: a bad answer always indicts the facts or the solver, never a forgotten stale field.

## Consequences
- Existing struct fields get audited against the litmus test during the Phase 1 schema-lock pass (`current_state` and `active_instance_count` are already flagged as caches; they must be marked non-authoritative or removed).
- Query architecture: solvers read facts, never write them; ingestion/editing writes facts, never conclusions.
- Vocabulary (glossary): ground fact vs entailment.
