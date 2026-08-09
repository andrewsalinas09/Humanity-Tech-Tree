# ADR-0043: Correct and scalable from the start — no hacking for convenience

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user rule ("That's how things die because they never get updated"), stated while ruling the UI stack

## Decision
1. **Contracts, data shapes, and interaction models are end-state-correct from day one.** The schema, the fact log, the verb surface, the tile/LOD protocol, URL structure, the rendering architecture — anything expensive to change under success — is designed for the target scale (billions of nodes, public traffic) immediately.
2. **Implementations may start modest ONLY behind a contract that never changes.** Postgres-behind-the-JSONL-log is legal (the log is the contract; the engine swaps invisibly). "Ship the DOM renderer now, rewrite in WebGL later" is ILLEGAL when the renderer shapes the interaction model — that is a known-wrong shape adopted for speed, i.e., the hack that never gets replaced.
3. **The test:** "if this succeeds, does this piece survive unchanged, swap invisibly behind its contract, or force a migration?" Only the first two are acceptable answers.
3b. **The freeze horizon is PUBLIC LAUNCH** (user clarification): internal iterations may be scrapped and rebuilt freely — research and ratified contracts carry forward; scaffolding is expendable. What is forbidden is carrying a known-wrong shape *across* the public-launch line, where permalinks, citations, and users make it permanent.
4. **Applied to the UI (the decision that prompted this):**
   - **D1 — street-view zoom over billions:** map-tile architecture from day one. Far zoom renders SERVER-COMPUTED AGGREGATES (density/structure tiles from the in-memory skeleton, ADR-0031), mid zoom renders family bubbles (ADR-0018 LOD), near zoom renders nodes with the full trust visual language. The client never receives a billion of anything; the tile protocol is part of the permanent contract. (Q-15 made concrete.)
   - **D2 — renderer chosen by research against target scale**, not by convenience (research running; WebGL/WebGPU-class required).
   - **D3 — layered DAG layout (ELK-class) in workers**; force-directed hairballs rejected; time flows one way because the graph does.
   - **D4 — SSR from the start**: every node is a crawlable permalink from the first public byte; framework chosen in the same research pass.
   - **D5 — Tailwind + primitive-component layer (shadcn pattern) + the trust visual language** defined once as tokens (red badge, band glyphs, UNKNOWN yellow, presumption dimming, shadow ghosting).
   - **D6 — the browser calls the SAME Service verbs** through a thin JSON facade (ADR-0040 one-surface); TanStack Query-class data layer.

## Why
Convenience hacks die in place: they work just well enough that replacing them never wins prioritization, until they're the reason the system can't grow. This project's premise is permanence — a graph meant to outlive its tools — so every load-bearing shape gets built once, correctly, and the only cheap starts permitted are the invisibly-swappable kind.

And the user's sharpest formulation: **"having billion scale from the start makes this an actual tool — a thing — not a demo / project."** Demos optimize for the screenshot; tools optimize for the millionth user's ordinary Tuesday. Every architecture choice here is the second kind.
