# ADR-0033: Continuous computed confidence alongside the discrete ladder

- **Status:** Accepted
- **Date:** 2026-08-10
- **Source:** user rulings, restart session 3 (endorsed the three-quantity separation; chose bands+hover display; motivation: "research quality and research tool that's cited, but also users have fun with it")

## Context
Three distinct quantities were being conflated: verification depth (what checking happened), epistemic confidence (how likely true given evidence), and source strength (count × quality × independence). ADR-0032's ladder covers the first; the user wants the second as a continuous 0–100; the third is an input, not a score.

## Decision
1. **Two computed dimensions per claim, never conflated:**
   - **Verification level (ADR-0032)** — discrete, process, event-derived. Drives workflows, queues, the red badge, and the verification game.
   - **Confidence score, 0–100** — continuous, evidence-derived: a versioned open formula `f(source count, source independence, source reliability, verification events, epistemic status, unresolved challenges, …)`. Computed at query time, never stored, never authored (ADR-0026). They diverge meaningfully (fresh claim with 5 gold sources: L2/conf 90; ratified claim with a newly challenged source: L5/conf dropping).
2. **Sources are first-class nodes** (WORK_PUBLICATION and kin). A citation is an edge claim→source; **source reliability is community-assessed on the source node** (the Wikipedia perennial-sources pattern) — so "2 independent gold-tier sources" and "5 blogs quoting each other" compute differently. Independence estimation (shared origin detection) is part of the formula.
3. **The formula is versioned and open.** It is contested *as a whole* (proposals to change it, like code), never per-claim — you cannot edit a score, only the facts beneath it. A formula change instantly re-scores the entire graph (the facts-only dividend). Formula version is shown in every trace.
4. **Display: bands by default, number + trace on hover** (user ruling). Browse shows a small set of visual bands (very-high / high / contested / weak / unsourced-red — the ADR-0030 red badge is the bottom band of this one scale); hover reveals the exact number AND the why: which sources, which checks, which challenges moved it. Never a naked number, never "100% true."
5. **A low score on a popular claim is a decomposition bounty.** "Microsoft created DOS" scores mid-band *because the history is genuinely fuzzy* (bought 86-DOS from Seattle Computer Products, adapted it, licensed to IBM) — the score is a smell detector pointing at claims that need resolution-splitting into finer facts that each score high. Truth never changes; resolution increases.

## Why (the dual-audience motivation, user's own)
The project must be simultaneously **research-grade** — citable, filterable to high floors, every number traceable to facts and a versioned formula — and **fun** — open to everyone, where red badges and contested bands are the game board. One fact base, two lenses. Continuous confidence gives researchers real signal (source strength moves the needle); bands + traces keep the display honest against false precision; the discrete ladder keeps the game legible.

## Consequences
- Formula v1 is a Phase 2/3 deliverable (with a golden-claim eval set, like the embedding evals); it starts simple and versions openly.
- Source nodes gain reliability-assessment machinery (community facts, same moderation rails).
- MCP reads return both dimensions + trace; filters accept floors on either.
- TB-045 (the DOS decomposition) added. Glossary: confidence score.
