# ADR-0031: Postgres-first backend; branching and versioning are application-level

- **Status:** PROPOSED — awaiting user ratification
- **Date:** 2026-08-10
- **Source:** three-stream research synthesis (`docs/research/2026-08-backend-synthesis.md`); supersedes the storage half of ADR-0010 (the in-memory-solver split survives)

## Context
ADR-0010 chose Neo4j in the old-LLM era, before the requirements matrix (Q-17) and the agent-first ruling (ADR-0029). Research across the 2026 landscape found: (a) the eliminating requirements — per-entity versioning, shadow-branch ChangeRequests, parallel commutative writes, engine swappability — are provided natively by *no* scalable graph engine; that layer is app-level everywhere; (b) at-scale precedent (Wikidata, OSM) is unanimously app-level changesets on a plain store; (c) the in-memory-solver split means the store only needs cheap fat subgraph reads, neutralizing graph engines' traversal advantage; (d) the graph-DB market churned violently in 2025–26 (Kuzu archived by Apple, TigerGraph distressed, Dgraph resold, ArangoDB relicensed), vindicating swappability as the top requirement.

## Decision
1. **PostgreSQL is the system of record**: append-only assertion tables (entities / entity_versions / assertions / change_requests / merge_log), edges list-partitioned by the 8 basis types (the ADR-0024 partition key becomes a physical partition), secondary indexes on qualifiers/categories/statuses/dates, pgvector for embeddings (sufficient through ~50M vectors; Milvus/Turbopuffer is the proven billion-scale jump).
2. **ChangeRequests are application objects** — the ADR-0013 shadow branch implemented as proposal objects whose apply is a commutative set-union of immutable assertions (CRDT discipline without a CRDT store); true conflicts route to review. Reverts are forward edits (OSM pattern).
3. **The solver runs in memory over fat subgraph reads** (unchanged from ADR-0010; solver language/runtime remains Q-16; LadybugDB-embedded is a candidate substrate).
4. **A thin custom MCP server exposes verb-shaped tools** (`propose_node`, `search_similar`, `link_nodes`, `attach_citation`, triage queues) with idempotency keys, per-agent rate budgets, and machine-readable typed rejections — never a raw-query wrapper (ADR-0029).
5. **The canonical truth is the exported fact log** (JSONL serialization defined with the v1 schema doc); any engine, including Postgres, is a replaceable index over it. Migration triggers documented in the synthesis watch list (FlureeDB, DoltgreSQL, Neo4j-at-scale).

## Why
Postgres is where the unavoidable app-level layer is cheapest and most transactional; MVCC handles agent-swarm write concurrency better than single-leader graph engines; operational knowledge is universal; licensing is permanently safe; and starting tiny is free. The things a dedicated graph engine would add (native deep traversal) are exactly the things the architecture doesn't need from the store. Choosing boring, revenue-independent infrastructure after a year in which three fashionable graph engines died or relicensed is the R9 lesson applied.

## Consequences
- ADR-0010 marked superseded-in-part (Neo4j choice); the fat-query/in-memory-solver pattern is reaffirmed.
- Phase 2 builds directly on Postgres (skipping the interim files/SQLite step — Postgres starts equally tiny and removes a migration).
- Q-17 → Resolved on ratification. Q-16 (solver runtime + API layer) remains open, narrowed: the API layer is the MCP server; the solver-language question stands.
- The v1 schema document (Phase 1 close-out) now includes the table sketch and the JSONL fact-log format.
