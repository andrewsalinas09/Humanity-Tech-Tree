# ADR-0049: Reputation mechanics — computed from facts, gently slashed

- **Status:** Accepted (ALL numeric parameters explicitly tunable — user: "no idea how the dynamics play out in real life")
- **Date:** 2026-08-09
- **Source:** user rulings (wire reputation before challenge voting; slash-table tuning "everything-it-earned is way too much")

## Context
ADR-0013 promised a trust chain and slashing; ADR-0032 promised verification events as facts; ADR-0046 split ink (activity) from reputation (trust). Challenges (structured disputes with voting) are ruled to sit ON reputation, so reputation wires first.

## Decision
1. **Reputation is COMPUTED from the fact log, never authored** (same constitution as verification levels, ADR-0032 §2). Verification events, challenges, and votes are FACTS (user ruling); reputation = f(those facts) per user. Auditable ("show the events behind this number"), never stale, demotion cascades automatically. `users.reputation` is a cache, refreshed after relevant events.
2. **Earning (verified work only — activity is ink's job):**
   - authored claim reaches L3 (machine-verified) **+1**; L4 (human-verified) **+3**; L5 (community-ratified) **+5** (increments are cumulative rungs)
   - performed a verification that stands **+1**
   - raised a challenge that is upheld **+3**
3. **Slashing (user-tuned: wrongness is cheap, fraud is expensive, malice is ruinous):**
   - claim demoted by upheld challenge / retraction-for-cause **−1** (flat; NO clawback of earned rep — good-faith wrongness must not erase a mostly-good record)
   - verified/vouched for content later found wrong **−2**
   - hallucinated/false citation caught **−4**
   - admin vandalism ruling **−25**
4. **Vesting (ADR-0013):** votes count only once the voter has ≥3 claims standing at L3+ (or is an admin). Vote weight = 1 + max(0, reputation).
5. **Agent↔operator linkage:** an agent's slash rolls up a fraction (0.5, tunable) to its operator — what makes "operators required" (ADR-0046) bite.
6. **Verification ladder events** (the facts these compute over, per ADR-0032): `verification.machine {assertion_id, verdict, model}` (L2→L3), `verification.human {assertion_id, verdict}` (L3→L4; N=2 independent humans ⇒ L5, tunable). Event facts flow through the log; the kernel View ignores them (they are history, not graph structure).
7. **Challenges** (per the same-day rulings): `challenge.open {subject, grounds, remedy: [verb calls]}`, `challenge.vote {support, reason}`, `challenge.resolve {outcome}` — all facts. Votes are reputation-weighted and ADVISORY; **an admin ratifies every passed challenge**; on upheld, the pre-staged remedy verbs execute under the resolver's identity with the challenge as provenance. Tombstone remedies still ride ADR-0047's gate.

## Consequences
- The 10-agent community experiment becomes runnable: agents author → get verified → vest → challenge → vote → admin ratifies; the reputation ledger moves and is fully explainable.
- MCP tools: verify_citation, confirm_verification, open_challenge, vote_challenge, resolve_challenge.
- Q-24 → Resolved. Q-03 (moderation params) gains concrete initial values, all tunable.
