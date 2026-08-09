# ADR-0032: The verification ladder — five computed levels from uncited to community-ratified

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user sketch ("maximum additions and maximum truthfulness"), fleshed out per their delegation; completes ADR-0030

## Context
ADR-0030 accepts everything and marks uncited content red. But "cited" vs "uncited" is too coarse: a plausible-looking citation may not support the claim (the hallucinated-citation failure mode documented in `docs/research/2026-08-agent-mcp-vector-stack.md`), and consumers need graded filters ("only well-verified content") without any submission ever being rejected.

## Decision
1. **Five levels, climbing on verification evidence** (not submitter species — provenance is separate, visible metadata):
   - **L1 — Uncited claim.** Red badge (ADR-0030). Accepted, never rejected.
   - **L2 — Cited, unchecked.** A source is attached; nobody has confirmed it supports the claim.
   - **L3 — Machine-verified.** An LLM verifier fetched the source and confirmed it supports the claim; verifier model+version+run recorded as a fact. Pennies per claim, infinitely parallel.
   - **L4 — Human-verified.** A person confirmed source-supports-claim (reviewer identity + event recorded).
   - **L5 — Community-ratified.** N independent, reputation-weighted human confirmations (N and weighting are ADR-0013 parameters, tunable). L5 content is **protected, not frozen**: edits require high trust + strong evidence (blast-radius machinery), but demotion remains possible — "never wrong" (ADR-0015) outranks "locked."
2. **Levels are computed, never stored** (ADR-0026). Stored facts: submissions (with human/agent provenance per ADR-0029), citation attachments, verification events, votes, challenges, retractions. Level = f(facts) per claim. Consequences: levels can never go stale, and **demotion is automatic** — a retracted source or upheld challenge instantly drops every claim resting on it.
3. **Per-claim granularity, subtree roll-ups.** Nodes, edges, and regional claims each carry their own level; views can show "this subtree is 87% L3+."
4. **Filters are first-class:** browse at L1+ (everything, honest mess — the default), L3+, L4+, L5-only. Export profiles (academic use) can pin a floor.
5. **Honest naming:** levels are verification depth, not truth probability. The UI never says "100% true"; it says "ratified by N independent verifiers" — a citable fact. Even L5 is demotable by new evidence.
6. **The economic pipeline this creates** (the point of the design): agents flood L1–L2 at swarm speed; machine verification lifts to L3 at scale and catches hallucinated citations; scarce human attention concentrates on L3→L4 where its leverage is highest; community consensus crowns L5. Verification games (click red → attach source; verify L2 → L3 confirmations) feed the reputation economy (ADR-0013).

## Why
This resolves the maximum-additions/maximum-truthfulness tension structurally instead of by compromise: nothing true is ever turned away, nothing unverified ever masquerades as verified, and every rung is a bounty someone (human or agent) is incentivized to climb. Computing levels from event-facts keeps the whole ladder inside the facts-only constitution and makes trust auditable end to end ("who verified this, with what model, when").

## Consequences
- MCP tools: `verify_citation` (agent-facing L2→L3), `confirm_verification` (human-facing L3→L4), vote endpoints; every read returns the computed level.
- Viewer: level is a visual dimension everywhere (red L1 badge from ADR-0030 is the bottom rung of one consistent scale).
- Moderation params (Q-03) gain: N and reputation-weighting for L5, challenge/demotion flows.
- TB-044 (hallucinated citation) added.
