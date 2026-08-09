# ADR-0029: Agent-first authoring; MCP is a first-class interface

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user directive, restart session 3 ("MCP needs to be first class as this is only tractable BECAUSE of LLMs")

## Context
The graph needs millions of nodes. The original vision already said the project is only now possible because of LLMs; this ADR makes the consequence explicit: the primary *authors* are LLM agents working in parallel, and humans are verifiers/directors (and can author when they want). Every interface, pipeline, and backend choice must be evaluated agent-first.

## Decision
1. **MCP is a first-class API surface, not an add-on.** The edit verbs (Refine/Abstract/Intercept/Componentize/Specialize), search-first existence checks (Q-20), check-queue triage, and fact-with-citation submission are exposed as MCP tools from the first prototype. The human UI is a *client of the same surface*.
2. **The write path is designed for parallel agent swarms:** high-throughput proposal submission into shadow branches (ADR-0013) — agents never write to master either; commutative merges leaning on order-independence (ADR-0023); machine-readable rejection reasons (linter verdicts, LCA diagnostics) so agents can self-correct.
3. **Humans are verifiers by default:** the moderation pipeline's human layer (vouching, review queues) is the trust bottleneck by design; agent throughput must never pressure human verification into rubber-stamping. Agent-generated content carries agent identity + model/version + prompt provenance as facts (ADR-0011 audit fields extended to agents).
4. **Agents get reputations too.** Blast-radius/vesting (ADR-0013) applies to agent identities: new agent pipelines earn trust on leaves before touching high-dependency-mass nodes; a pipeline that produces rejected edits loses standing, exactly like a human account.
5. **Backend requirements are derived agent-first** — see the Q-17 requirements matrix (parallel write throughput, cheap fat reads for context assembly, machine-verifiable diffs).

## Why
A human-first design with agents bolted on caps the graph at human authoring speed — the pre-LLM failure mode. An agent-first design with humans as the trust layer matches the actual economics: generation is cheap and parallel, verification is scarce and precious. The moderation architecture (ADR-0013) was already shaped like this — shadow branches + review queues are exactly an agent-scale ingest funnel.

## Consequences
- Every Phase 2+ component ships MCP-first; UI follows.
- Q-17 backend evaluation gains hard requirements: R5 (parallel commutative writes), R8 (MCP-friendly semantics, cheap subgraph reads).
- The check-queue pipeline (Q-04) is symmetric: LLM proposes, human confirms — the same loop whether triggered by a human edit or an agent sweep.
- Moderation parameters (Q-03) must be tuned for agent-swarm scale, not forum scale.
