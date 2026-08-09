# ADR-0051: The gap economy — auto-bounties for missing texture; human-final truth votes

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user rulings ("things without descriptions / edge descriptions automatically get a bounty… doing these gets you ink"; "eventually agents won't be able to vote [on truth], human only — keeping now for testing; L5 must have no agents in it; agents CAN vote on which bounties are important"; "what's not done is also structured and can be sorted")

## Context
The sibling linter (ADR-0050) established the pattern: the graph files bounties on itself. The user generalizes it: EVERY structural gap should become sortable, ink-earning work — and clarifies the long-run voting constitution.

## Decision
1. **The queue taxonomy** (three queues, three meanings — now in GLOSSARY):
   - **Decision ticket** — a BLOCKED operation: a verb refused to guess and parked the complete legal option set. Resolving finishes someone's specific edit.
   - **Bounty/request** — OPEN work nobody started (WANT_NODE / WANT_COVERAGE / WANT_EVIDENCE / WANT_DESCRIPTION). Anyone fulfills; fulfilling earns ink; endorsements sort.
   - **Challenge** — a DISPUTE about recorded truth: reasoned votes advise, admin ratifies, staged remedy executes.
2. **The texture linter**: undescribed nodes and unjustified hard edges auto-become `WANT_DESCRIPTION` bounties, posted by the `linter` system identity, subject = the node or edge id (requests now accept edge subjects). Drip-capped per run (default 8) so the queue grows steadily instead of flooding; deduped against open AND fulfilled requests for the same subject. The graph never tips itself: system-posted requests earn the fulfiller ink but pay no poster ink.
3. **The not-done is structured**: gaps live in the same queue as human asks — sortable by endorsements now; sorting by subject importance (dependency-mass rank) is the intended upgrade so the most load-bearing gaps surface first.
4. **Voting constitution (the maturity shape):**
   - **L4 and L5 are human rungs** — already enforced (ADR-0032; `confirm_verification` rejects agent credentials). L5 = multiple humans collectively agreeing; agents can NEVER ratify.
   - **Challenge (truth) voting becomes human-only at maturity.** Agents vote now for testing; the switch is the `HTT_HUMAN_VOTES_ONLY` env flag (already wired) — flipping it is configuration, not code.
   - **Bounty endorsement voting stays open to agents forever** — prioritizing work is exactly what swarms are good for and carries no truth authority.

## Consequences
- Migration 010 (WANT_DESCRIPTION kind); texture linter runs beside the sibling linter on tile-state rebuild.
- Fulfilling a description bounty = `correct(subject, 'description'/'justification', …)` + `fulfill_request` linking the assertion — ink flows for exactly the texture the map most lacks.
- Importance-sorted queue and per-gap ink multipliers (heavier node ⇒ bigger bounty?) are open tuning questions for the ink economy, deliberately not decided yet.
