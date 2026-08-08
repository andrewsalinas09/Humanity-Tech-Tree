# ADR-0013: Four-layer moderation: blast radius, shadow branches, circuit breakers, trust chain

- **Status:** Accepted (design level; parameters tunable)
- **Date:** ~2026-01
- **Source:** README brain-dump; long-chat digest

## Context
An openly editable graph of all human knowledge is a vandalism magnet, and its most valuable nodes (Physics, Steam Engine) are exactly the ones a bad edit damages most. Bots can vote-stuff any purely social review system.

## Decision
1. **Blast radius:** edit rights scale inversely with a node's `dependency_mass` — new users < 5 dependents, verified < 100, elders/admins for core nodes.
2. **Shadow branches:** no direct writes to master. Every edit is a `ChangeRequest` (proposed branch) visible to its author, amendable by reviewers, merged only after approval — "Git for History."
3. **Circuit breakers:** auto-reject cycles (except through OPTIMIZES edges) and edits orphaning many children; a cheap embedding model flags semantically absurd connections (Banana → Nuclear Bomb) and freezes anomaly clusters for admin review.
4. **Trust chain:** merges require 3 vouches; vouching for vandalism costs the voucher reputation ("if you vote for spam, you die"), making review self-policing.

Bot defense: reputation vesting (votes only count after accepted leaf contributions), embedding sentinel for coordinated anomalies, Neo4j graph analysis for Sybil cliques (closed groups that only vote for each other). Safety net: atomic rollback of graph sections (enabled by ADR-0011).

## Why
Each layer catches what the previous one misses: permissions stop drive-by damage, isolation makes review possible, automation catches structural/semantic nonsense cheaply, and reputation-at-stake makes human review honest. Damage capacity proportional to trust earned.

## Consequences
Requires user accounts, reputation accounting, an embedding service, and review-queue UX before public write access — hence read-only first (ADR-0014). Exact thresholds (5/100, 3 vouches, −5 auto-hide) are tunable parameters, not commitments.
