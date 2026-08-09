# ADR-0030: Citation is first-class; submissions are never citation-gated

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user directive, restart session 3

## Context
The project lives or dies on citability (ADR-0029 context, VISION). But requiring citations at submission time kills usability — contributors (human or agent) mid-rabbit-hole would abandon edits, and the graph would lose true content. Meanwhile the research on LLM-built graphs (docs/research/2026-08-agent-mcp-vector-stack.md) documents the "plausibility trap": uncited-but-plausible claims pass casual review.

## Decision
1. **Never reject a submission for missing citations.** Structural/vandalism review (ADR-0013) still applies; citation absence alone is never grounds for rejection.
2. **Uncited content is instantly, loudly marked:** `[needs citation]`, red, visually unmissable at every zoom level. Verification status is a first-class visual dimension of the graph, not metadata buried in a panel.
3. **The badge is computed, never stored** (ADR-0026): empty citations list → red. Attaching a source clears it immediately; removing the last source restores it. No stale flags possible.
4. **Citation repair is a game:** red nodes/edges are standing bounties — click red, find a source, attach it, earn reputation. Joins the existing bounty loops (unrealized nodes, flagged edges, missing-node contradictions).
5. **Granularity:** citations attach per claim — nodes, edges, and regional-availability entries each carry their own sources (fields already exist per ADR-0011 provenance); the badge computes at each granularity, and an entity is only fully "clean" when its claims are covered.
6. **Trust-weighting downstream:** verifiers, solvers, and exports MAY weight or filter by citation status (e.g. "cited-only view" for academic use), but the default browse shows everything with honest badges — show the mess (VISION §3).

## Why
This is the prime directive applied to provenance: an uncited true claim is *incomplete* (missing its source), not wrong — rejecting it would discard truth for a formality, while displaying it unmarked would launder unverified content as verified. The loud-badge middle path preserves both usability and citability, and turns the gap itself into contributor fuel. It is also the practical mitigation for the plausibility trap at agent-swarm scale: agents can flood proposals, but nothing *looks* trustworthy until sourcing catches up — verification remains the human-paced bottleneck by design (ADR-0029).

## Consequences
- Viewer requirement: red-badge rendering at every zoom level; a "citation debt" count per subtree so dense areas show how much red is inside.
- MCP tools return citation status in every read; `attach_citation` is a first-class verb.
- Reputation systems (ADR-0013) reward citation repair like other accepted contributions.
