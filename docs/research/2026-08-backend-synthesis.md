# Backend synthesis — August 2026

Synthesis of the three research streams (`2026-08-graph-engines.md`, `2026-08-versioned-stores.md`, `2026-08-agent-mcp-vector-stack.md`). All three converged independently.

## The convergent finding

The requirements that *eliminate* candidates (R3 versioning, R4 branching, R5 parallel commutative writes, R9 swappability) are ones **no scalable graph engine provides natively** — that layer is application-level *everywhere*. So the engine question reduces to: where is the app-level fact-store + ChangeRequest layer cheapest, most transactional, and least lock-in? Answer from all three streams: **PostgreSQL**.

Supporting convergences:
- **At-scale precedent is unanimous** (Wikidata 2.5B+ edits, OSM changesets): app-level revisions/changesets on a plain store, review as application logic, reverts as forward edits. Nobody at scale uses storage-level branching.
- **The in-memory-solver split (ADR-0010) survives and neutralizes the graph-engine advantage:** the store only needs cheap fat subgraph reads; deep traversal happens in the solver. The 8-type edge basis maps directly onto Postgres list partitioning — the ADR-0024 partition key becomes a literal physical partition.
- **MVCC beats single-leader graph DBs for agent-swarm writes** (R5), and CRDT *discipline* (grow-only immutable assertions, UUID identities, commutative CR-apply as set-union, true conflicts routed to review) satisfies order-independence without adopting a CRDT store — ElectricSQL's own retreat from CRDTs to API-mediated writes is the cautionary precedent.
- **Vector path:** pgvector in the same database to ~50M vectors (covers Phase 2-4 easily), with Milvus/Turbopuffer as the proven billion-scale jump (Notion 10B+ vectors on Turbopuffer). Matryoshka embeddings: short truncated vectors for the dedup gate, full for rerank.
- **MCP:** existing graph-DB MCP servers are raw-Cypher wrappers — wrong abstraction. Build a thin custom MCP server exposing the wizard verbs (`propose_node`, `search_similar`, `link_nodes`, `attach_citation`) with idempotency keys, per-agent rate budgets, machine-readable typed rejections (the 2026-07 MCP spec makes structured tool errors first-class).

## The 2025–2026 churn that vindicates R9 (swappability)

- **Kuzu**: acquired by Apple, archived Oct 2025 with no notice (LadybugDB is the surviving fork — attractive later as an *embedded solver-side* engine: columnar Cypher, Arrow zero-copy, Icebug snapshots).
- **TigerGraph**: layoffs, failed funding. **Dgraph**: two ownership changes. **ArangoDB**: BUSL + 100GiB production cap. All eliminated.
- **Neo4j** remains #2: healthiest ecosystem, proven 100TB/trillion-edge scale (Infinigraph, Sept 2025) — but behind a steep proprietary cost cliff, and its versioning/branching is equally DIY. It stays a viable later migration target *because* the schema/serialization is the commitment.

## Watch list with decision triggers

- **FlureeDB** (GA June 2026): the only native branch/merge graph store marketed explicitly for agent-proposed edits; benchmarked on Wikidata-scale triples. Revisit if: it survives 18 months, BSL terms prove acceptable, and our app-level CR layer becomes a maintenance burden.
- **DoltgreSQL** leaving beta; **TerminusDB** community growth; **LadybugDB** maturity (as solver substrate); Postgres+pgvectorscale scaling limits (~50M vectors) → Milvus/Turbopuffer.

## Proposed stack (v1)

1. **System of record: PostgreSQL** — append-only assertion tables (entities / entity_versions / assertions / change_requests / merge_log per the versioned-stores sketch), edge table list-partitioned by the 8 basis types, qualifier/category/status secondary indexes, pgvector for embeddings.
2. **ChangeRequests are application objects** (the ADR-0013 shadow branch), applied as commutative set-union of immutable assertions; review/trust/vouching is app logic (it always was going to be).
3. **Solver: in-memory over fat subgraph reads** (language TBD — Q-16; LadybugDB embedded is a candidate substrate later).
4. **MCP server: custom, thin, verb-shaped** — the ADR-0012 verbs + Q-20 search + ADR-0030 citations as typed tools; the human UI is a client of the same surface (ADR-0029).
5. **Export discipline from day one:** canonical JSONL serialization of the fact log; the engine is swappable because the log is the truth (R9).
