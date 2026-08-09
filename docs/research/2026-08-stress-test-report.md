# Architecture stress test — 2026-08-08

Adversarial red-team of the full design (34 ADRs, 46 TB cases at time of test), run as a 17-agent workflow: 7 finders locked to distinct attack dimensions (temporal, mutation, errors, solver, concurrency, trust, identity), forbidden from re-reporting TESTBED-covered ground → dedup (28 raw → 26 distinct) → skeptic verifiers defending the architecture, walking each scenario through documented mechanisms.

**The complete adversarial record — every finding's full scenario and every verifier's full adjudication — is preserved for future agents in `stress-test-2026-08/` (one file per dimension).**

## Verdict: 0 BREAKS · 17 PARTIAL · 9 HANDLED

No finding survived verification as a fatal break. Every PARTIAL reduced to a small missing rule — codified as **ADR-0035 H1–H17** with test cases TB-047–TB-063. The 9 HANDLED findings below are validated defenses: attacks the existing machinery already covers by composition (each verifier walk-through is effectively a free worked example).

## The 9 refuted attacks (what the design already survives)

1. **Thera's bimodal dating dispute** (two camps, a century apart) — competing dated claims with epistemic status + uncertainty, not one blurred DatePoint; the dispute is representable content.
2. **Patient-zero rollback vs a year of legitimate downstream work** — rollback is forward-editing (OSM pattern); downstream work survives as facts; dangling references become stubs/bounties, never destruction.
3. **False "unconditional" via a constraint-pruned OR branch** — conditionality and pruning are both entailments over the same expression; the solver evaluates them together, no stored conclusion to go stale.
4. **Concurrent requirement-tree CRs racing a singleton slot** — tree-valued fields pin to field-level CR conflict granularity; races route to review.
5. **Vouch-threshold reads racing reputation changes** — thresholds evaluate at merge time inside the transactional apply; post-merge slashes demote via the event machinery.
6. **Decomposition laundering a false synthesis into green micro-facts** — the synthesis claim is itself an edge needing its own citation and level; green parts never confer greenness on the composition edge.
7. **iPhone 15 Pro generation-by-trim matrix** — sub-family nodes (ADR-0020) + iteration records compose; the "no legal attachment point" claim dissolved under the truth-granularity rule.
8. **Qualifier homonym forks breaking the split escape hatch** — qualifiers are machine-invisible by construction (ADR-0024), so homonyms cannot corrupt machine behavior; canonicalization (ADR-0004 pattern) is hygiene, not correctness.
9. **Era-erasing capability-router hubs poisoning earliest-possible** — routers are nodes with dated edges like any other; the widening ratchet never erases dates; coarse hubs are TB-001-class resolution debt, prunable and refinable.

## The 17 hardening rules

See ADR-0035. Distribution: temporal ×3 (method-source supersession, interval semantics, timeline coherence), mutation ×4 (redirect acyclicity, un-merge verb, merge payloads, override re-validation), errors ×2 (verifier discreditation, post-merge breaker recheck), solver ×4 (composed-mode evaluation, exclusion×expression, shadow×implicit-AND, claim-equivalence), trust ×3 (L3 injection hardening, formula governance, operator-level independence), identity ×1 (poly-hierarchy composition).

## Reading of the result

The architecture's core bets — facts-only, never-wrong, order-independence, computed entailments, the edge basis — took the full force of 7 adversarial lenses and bent nowhere. Every gap found was a *composition seam*: two sound mechanisms meeting without a written rule for their interaction. That is exactly the failure class a paper-phase stress test exists to catch, and exactly the class that becomes catastrophic if discovered at a billion nodes instead.
