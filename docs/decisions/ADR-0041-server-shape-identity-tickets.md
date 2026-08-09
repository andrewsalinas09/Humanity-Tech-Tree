# ADR-0041: Server shape — dual transport, server-stamped identity, tickets from day one

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user rulings on the three MCP-server decisions

## Decision
1. **Dual transport, one core.** The service layer (verb executor over PgFactLog + kernel) is transport-agnostic; it ships with BOTH faces: a local stdio MCP launcher (attach your Claude Code today) and a streamable-HTTP MCP service (Docker, so others can attach theirs — deployable from the start). Cost of both doors ≈ two thin entrypoints.
2. **Identity is a per-connection credential, stamped server-side.** Tokens (hashed) map to identities `{type: human|agent, id, model?, version?}` in an `identities` table; the SERVER stamps `author` on every fact — caller-supplied identity is never trusted. Rate budgets are per-identity counters enforced server-side (generous defaults now; the enforcement point exists from fact one). Rationale, user's words: "We need security. This WILL be griefed."
3. **Decisions are tickets, built properly now.** A verb returning a Decision persists a `decision_tickets` row (verb, params, reason, options, opened_by); `resolve_decision(ticket_id, choice)` merges the choice into the params, re-compiles, applies, and stamps `resolved_by`. This IS the check-queue substrate (Q-04): an agent can park a question above its pay grade and a human (or better model) answers later — the pick is provenanced content either way.
4. **Read-side principle (future, recorded now):** semantic services (existence gate judgments, triage suggestions) use whatever model is cheapest on the frontier (user cites OpenAI Luna/Tera) — but ALWAYS through the same compilable-question tools: the LLM never queries a billion nodes; it asks typed questions and receives computed answers. ADR-0040's transaction rule, extended to reads.

## Consequences
- `server/` package: service layer + identity/budget + tickets + two entrypoints; migration 002 (identities, decision_tickets, searches, wall-clock on facts for budget windows).
- `search_similar` v1 is deterministic (name/alias matching) issuing receipts; `propose_node` requires a receipt (the unskippable gate); the semantic upgrade slots behind the same tool later.
- Griefing hardening (Q-03 parameters, blast radius enforcement) attaches to the identity spine built here.
