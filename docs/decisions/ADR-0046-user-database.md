# ADR-0046: The user database — identity ≠ credential ≠ score

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user rulings (leaderboard tab request; "there should be a user database, let's design"; four AskUserQuestion rulings; "don't use the word karma")

## Context
The server spine (ADR-0041) had one `identities` table doing three jobs: credential (token hash), identity (who), and score (points). That conflation meant a lost token was a lost identity, agents could exist without accountability, and the gamified score was about to be conflated with trust.

## Decision
1. **Three concepts, three homes.**
   - **`users`** — the durable public identity. `user_id` is a **chosen handle** (GitHub-style) and is exactly what gets stamped into facts as `author.id`; prestige attaches to a recognizable name. Plus display_name, kind (human|agent|system), bio/link.
   - **`credentials`** — tokens are disposable pointers: many per user, rotatable, revocable (`revoked_at`), each with its own budget. Losing a token no longer loses an identity.
   - **Scores live on the user**, split by nature (below).
2. **Agents require an operator** — a `users` row cannot be `kind='agent'` without `operator` referencing a user (DB CHECK + service validation). The blame corollary (ADR-0042) extended: no orphan bots; slashing and accountability roll up to people.
3. **Two scores, never mixed:**
   - **`ink`** — the gamified contribution score ("your ink on the record"; the nodes are books, the substrate is a fact log — the metaphor is native, and deliberately NOT Reddit's word). Monotone up: fulfilling requests earns 3 + endorsements; posting a later-fulfilled request earns 1. Fun, prestige, leaderboards.
   - **`reputation`** — ADR-0013 trust: earned by verified work, **slashable** when facts are retracted for cause, gates privileges. Grinding ink can never buy trust.
4. **Everything is public.** Contribution history is already public-by-architecture (author-stamped fact log); profiles show ink, reputation, history, fulfilled requests, and operated agents. History is a **view over the log, never stored state**.
5. Naming registers the project's ambition: the vocabulary (ink, reputation, citations with locators) must read cleanly in an academic paper — this graph aspires to be citable by real research.

## Consequences
- Migration 004: `users` + `credentials`, data migrated, old `identities` dropped.
- `create_identity(token, {type, id, operator?, display_name?})` creates user + first credential; rejects operator-less agents. `revoke_credential(token)` exists.
- Leaders tab: leaderboard (ink, reputation, fact counts) with clickable profiles (contribution lines → map focus).
- Future (not yet): real login flows mapping to user_id; operator self-service token provisioning for their agents (the ADR-0041 provisioning gap); reputation mechanics wiring (ADR-0013 verification/slashing events).
