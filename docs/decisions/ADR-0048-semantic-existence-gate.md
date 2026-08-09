# ADR-0048: The two-lane semantic existence gate (resolves Q-20)

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** the first autonomous agent's friction report (13/20 concept queries found nothing on exact matching; it discovered related nodes only by walking edges) + user rulings (both local AND API embeddings; semantic matches advisory-only)

## Context
Q-20 always knew the existence gate needed semantics at scale; the photolithography bounty run proved it empirically. Meanwhile ADR-0045/description work had already created the missing ingredient: every node carries a 2–3 sentence description — the embedding text (a name alone embeds terribly).

## Decision
1. **Two lanes in `search_similar`.** Lane 1: exact/substring over names+aliases (unchanged; still the only thing that FORCES duplicate Decision tickets). Lane 2: semantic — top-k nearest nodes by cosine over embeddings of `name + aliases + category + description`, returned WITH descriptions and scores.
2. **The caller judges.** No LLM inside the server transaction (ADR-0040) — the callers are LLMs; the gate's job is recall + rich candidates, not verdicts. Semantic matches are ADVISORY (user ruling): TB-032's create-don't-merge asymmetry stands — err toward creating, heal by merge.
3. **The receipt records both lanes.** "You were shown photolithography at 0.67 and created 'chip patterning process' anyway" is attributable forever — future reputation input.
4. **Both providers** (user ruling): LOCAL (fastembed BGE-small-en-v1.5, ONNX, offline, free) is the always-available default; an OpenAI-compatible API lane activates via `HTT_EMBED_API_KEY`/`HTT_EMBED_API_URL`/`HTT_EMBED_API_MODEL`. Embeddings are DERIVED data (ADR-0026): keyed by (node_id, model), text-hash gated re-embedding, rebuildable — the model is swappable forever.
5. **Storage now vs scale:** dev-scale = JSONB vectors + Python KNN (fine to ~10^4). The production upgrade is pgvector + HNSW — a container swap and reindex, storage-only, no contract change (the vanilla postgres:16 container lacks the extension; noted for the production bake).
6. **Browse affordance:** `list_nodes(category?)` — the graph is enumerable; search is not the only lens (agent friction).
7. The gate DEGRADES, never blocks: if the semantic lane fails (no model, no network), lane 1 still issues receipts.

## Consequences
- Q-20 → Resolved. The agent's failed queries now resolve ("integrated circuit chip"→cpu 0.70, "silicon wafer"→silicon 0.66, "chip patterning"→photolithography 0.67).
- Embed-on-search with hash gating ≈ embed-on-create without a write-path hook; at swarm scale move refresh to the apply path.
- The description-nag now has teeth: an undescribed node is nearly invisible to the semantic lane — quality feeds discoverability feeds dedup.
