# Graph Database Engine Research — August 2026

**Project:** Humanity Tech Tree — knowledge graph targeting billions of nodes/edges (starting tiny), authored in parallel by LLM agent swarms, consumed by a solver doing deep recursive dependency traversals.

**Method:** Web research conducted 2026-08-08 against the current state of the market (versions, licenses, corporate events through mid-2026). Sources cited inline.

---

## Requirements recap (from ADRs)

| ID | Requirement |
|----|-------------|
| R1 | Scale path: billions of nodes/edges eventually, TB-scale payloads; must start tiny/cheap (single machine) |
| R2 | Deep traversal: 10–100-hop recursion; fat subgraph extraction into in-memory solver; edge-type partition pruning (8 edge types) |
| R3 | Immutable facts + per-entity version history, atomic rollback |
| R4 | Branching (git-like propose/merge shadow branches) — native or cheap to build |
| R5 | High-throughput parallel writes with commutative merge semantics |
| R6 | Vector/ANN for per-node embeddings (billions), native or clean sidecar |
| R7 | Secondary indexes (slugs, categories, enum statuses, decimal dates) |
| R8 | Machine-friendly API for LLM/MCP agents: cheap subgraph reads, clean diffs |
| R9 | Self-hostable, sane license, clean export story (engine must be swappable) |

---

## The 2024–2026 landscape shift (context that changes the decision)

The market moved a lot since 2024, and several "obvious" 2024 answers are no longer safe:

- **Kuzu is dead.** Kùzu Inc. was acquired by Apple and the GitHub repo was archived on 2025-10-10 with no notice ([The Register](https://www.theregister.com/software/2025/10/14/kuzudb-graph-database-abandoned-community-mulls-options/1142229)). Three forks emerged: **LadybugDB** (Arun Sharma, community, positioned as the 1:1 successor), **Bighorn** (Kineviz), and **RyuGraph** ([gdotv 2025 recap](https://gdotv.com/blog/yearly-edge-graph-technology-news-recap-2025/)). LadybugDB is the one with real momentum (see profile below).
- **Dgraph changed hands twice.** Hypermode (2023) → **Istari Digital** (Oct 2025) ([gdotv recap](https://gdotv.com/blog/yearly-edge-graph-technology-news-recap-2025/), [Hypermode announcement](https://hypermode.com/blog/dgraph-part-of-hypermode)). v25 opened former enterprise features by default, but stewardship stability is unproven.
- **TigerGraph is in corporate distress.** ~30% layoffs (90 people), failed funding round, poor employee sentiment ([TrueUp](https://www.trueup.io/co/tigergraph/layoffs), [Glassdoor](https://www.glassdoor.com/Reviews/TigerGraph-Reviews-E1145722.htm)). Product pivoted to the Savanna managed cloud.
- **ArangoDB rebranded to arango.ai** and pivoted to an "AI-native contextual data platform"; v3.12 moved from Apache 2.0 to **BUSL 1.1**, and prepackaged Community binaries carry a 100 GiB production dataset cap + non-commercial restriction ([ArangoDB licensing update](https://arangodb.com/2024/02/update-evolving-arangodbs-licensing-model-for-a-sustainable-future/), [ORIX investment](https://www.orix.com/deals/arangodb-secures-strategic-investment-from-orix-usa-to-power-the-future-of-ai-native-data-infrastructure/)).
- **GQL (ISO/IEC 39075:2024) is real and gaining adopters** — the first new ISO database language since SQL (1987). Full-compliance implementations so far: Google Spanner Graph, Ultipa, GraphLite; Microsoft Fabric ships a GQL graph surface ([gqlstandards.org](https://www.gqlstandards.org/), [Neo4j on GQL](https://neo4j.com/blog/cypher-and-gql/gql-international-standard/), [MS Fabric GQL guide](https://learn.microsoft.com/en-us/fabric/graph/gql-language-guide)). Cypher-family skills transfer; query-language lock-in risk is declining.
- **Graph+vector+MCP converged.** Every serious engine now ships vector indexes and an MCP server; Graphiti (Zep) + FalkorDB/Neo4j is the de-facto agent-memory stack ([Graphiti](https://github.com/getzep/graphiti), [FalkorDB MCP](https://www.falkordb.com/blog/mcp-knowledge-graph-graphiti-falkordb/), [Neo4j MCP](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)).
- **LDBC rebranded to the Graph Data Council** (Sept 2025); LDBC SNB remains the only neutral benchmark, with scale factors moving toward SF100,000 (billions of nodes) ([gdotv recap](https://gdotv.com/blog/yearly-edge-graph-technology-news-recap-2025/)).
- **A wave of tiny new Rust engines** (Grafeo, OverGraph, GraphLite, HelixDB, Samyama-style research systems) appeared 2024–2026 — mostly pre-1.0, single-maintainer, or research code ([lib.rs listing](https://lib.rs/database-implementations), [Grafeo](https://grafeo.dev/), [OverGraph](https://github.com/bhensley5/overgraph)).

**Meta-observation:** no mainstream property-graph engine natively provides R3 (immutable per-entity history) or R4 (git-like branching). The only engine that does — TerminusDB — is weak on R1 scale. Versioning/branching will be an application-layer design on any engine you'd actually run at billions of edges. That pushes the decision toward engines that make append-only, diffable, exportable data models *easy*, rather than engines with the fastest 3-hop benchmark.

---

## Candidate profiles

### 1. Neo4j

- **Version/license (Aug 2026):** Calendar versioning; stable **2026.05/2026.06** ([Wikipedia](https://en.wikipedia.org/wiki/Neo4j), [endoflife.date](https://endoflife.date/neo4j), [ops manual](https://neo4j.com/docs/operations-manual/current/introduction/)). Community Edition **GPLv3** (single instance, no clustering/sharding); Enterprise is commercial open-core ([Neo4j open-core FAQ](https://neo4j.com/open-core-and-neo4j/)).
- **Scale story:** The strongest in the industry. Trillion-relationship demo (200B+ nodes, 1000+ machines) ([PR](https://www.prnewswire.com/news-releases/neo4j-breaks-scale-barrier-with-trillion-relationship-graph-301314720.html)); **Infinigraph** (Sept 2025) adds property-sharding HTAP at **100TB+** in a single logical graph — but it's a separate Enterprise subscription tier, Early Access self-managed, coming to AuraDB ([launch PR](https://www.prnewswire.com/news-releases/neo4j-launches-infinigraph-the-most-scalable-graph-database-for-unified-operational-and-analytical-workloads-at-100tb-scale-302545785.html), [SiliconANGLE](https://siliconangle.com/2025/09/04/neo4j-unifies-real-time-transactions-graph-analytics-scale/), [sharded property DB docs](https://neo4j.com/docs/operations-manual/current/scalability/sharded-property-databases/configuration/)).
- **Traversal:** Index-free adjacency; good at 10–100 hops via variable-length patterns / GDS projections; Cypher 25 current. Fat subgraph extraction well-supported (GDS Arrow export).
- **Versioning/branching:** None native. Composite/multi-database gives coarse isolation, not merge.
- **Vector:** Native HNSW vector index, GA, positioned for billions of vectors with Infinigraph ([Modern DataTools review](https://www.modern-datatools.com/tools/neo4j)).
- **Writes:** Single leader per database (causal cluster); write throughput is a known ceiling vs. distributed engines.
- **Ecosystem/momentum:** Largest community, first-class MCP servers, LLM-framework integrations everywhere ([Neo4j MCP](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)).
- **Fails/risks:** R1 cost cliff — the free tier ends at one GPLv3 instance; billions-scale means Enterprise/Infinigraph pricing. R3/R4 DIY. R5 moderate. R9 partial: self-hosting CE fine, but the scale features are proprietary; export (dump/CSV/Arrow) is clean.

### 2. PostgreSQL (+ pgvector, optional Apache AGE) — "Postgres as a graph"

- **Version/license:** PostgreSQL 18 current major line; PostgreSQL License (BSD-like). **Apache AGE 1.6.0** supports PG 11–18, latest release Jan 2026 (row-level security, id-column indexes); team is moving master to PG18 ([AGE releases](https://github.com/apache/age/releases), [roadmap discussion](https://github.com/apache/age/discussions/2305), [release notes](https://age.apache.org/release-notes/)).
- **Scale story:** Single-node Postgres comfortably runs multi-TB with partitioning; beyond that Citus/sharding or engine swap. Not a billions-of-edges *traversal* engine, but a proven billions-of-rows *store*.
- **Traversal:** Recursive CTEs (or AGE Cypher) handle bounded recursion fine when fan-out is controlled; 100-hop mega-fanout traversals are the weak spot — but the project's ADR already plans to extract subgraphs into an in-memory solver, which converts R2 into "cheap fat reads," a Postgres strength. Edge-type pruning maps directly to native list-partitioned edge tables (8 partitions by edge type).
- **AGE caveats:** AGE is a modest-velocity Apache project, a Cypher *subset*, with ABI breakage incidents on PG minor releases ([Crunchy Data near-miss](https://www.crunchydata.com/blog/a-change-to-relresultinfo-a-near-miss-with-postgres-17-1), [Azure PG17 issue](https://learn.microsoft.com/en-my/answers/questions/5817689/unable-to-enable-apache-age-extension-on-azure-pos)). Treat it as optional sugar, not the foundation; plain SQL schema + recursive CTEs is the durable core.
- **Versioning/branching:** Not native, but the *easiest* engine to build R3/R4 on: append-only fact tables, entity-version rows, branch-id columns or branch-delta tables, transactional merge — all standard SQL patterns with ACID guarantees.
- **Vector:** pgvector (HNSW/IVFFlat) is the most-deployed vector index on earth; billions of vectors needs partitioning/pgvectorscale or a sidecar, which the ADR allows.
- **Writes:** MVCC, real parallel writers, `INSERT ... ON CONFLICT` for commutative merge — best-in-class for R5.
- **Fails/risks:** R2 raw deep-traversal performance (mitigated by solver architecture); graph ergonomics are DIY; billions-of-edges multi-hop OLAP will eventually need a read-side companion (see LadybugDB/DuckPGQ).

### 3. LadybugDB (the Kuzu successor)

- **What/version:** Community fork of Kuzu, permissive (MIT lineage), self-described "DuckDB for graphs" / graph-lakehouse. **v0.17.0 (2026-05-28)** shipped Icebug Format v1 (Iceberg-style table format), Arrow/Parquet zero-copy, SQL pushdown, DuckDB-storage interop, object-store connectivity; roadmap: sparse tensors for embeddings, GPU analytics ([ladybugdb.com](https://ladybugdb.com/), [v0.17.0 post](https://blog.ladybugdb.com/post/graph-lake-icebug-format/), [Data Quarry: From Kuzu to Ladybug](https://thedataquarry.com/blog/from-kuzu-to-ladybug/)).
- **Inherited capabilities:** Kuzu's columnar storage, Cypher, vector + full-text indexes, embedded in-process operation, demonstrated 115M-node Wikidata analytics; Kuzu historically handled billions of edges on a single beefy machine.
- **Traversal:** Vectorized columnar joins + factorized execution — excellent for exactly the "extract a fat subgraph fast" pattern; native Arrow output feeds an in-memory solver with zero copies.
- **Versioning/branching:** Icebug (Iceberg-like snapshots) points at time-travel/branching semantics at the storage layer — potentially the cheapest R3/R4 substrate of any graph-native engine, but v1-new.
- **Fails/risks:** R5 — embedded single-writer process, no server/concurrent-writer story yet; R1 growth path is "bigger machine + object store," not distributed. Biggest risk is project risk: a months-old fork with a small unfunded team and no company behind it ([Register on fork uncertainty](https://www.theregister.com/software/2025/10/14/kuzudb-graph-database-abandoned-community-mulls-options/1142229)) — though the upstream abandonment also proves the value of keeping the engine swappable (R9).

### 4. FalkorDB

- **Version/license:** Active; core under **SSPLv1** (self-hosting fine; forbids offering it as a service), GraphRAG-SDK Apache 2.0; a next-gen **Rust rewrite** is underway ([FalkorDB GitHub](https://github.com/falkordb/falkordb), [falkordb-rs-next-gen](https://github.com/FalkorDB/falkordb-rs-next-gen)).
- **Architecture:** Redis-module, all-in-RAM, GraphBLAS sparse-matrix traversal; v4.14.10 cut memory ~30% via compact storage ([design docs](https://docs.falkordb.com/design/), [memory release](https://www.falkordb.com/news-updates/falkordb-v4-14-10-memory-optimization-compact-storage/)).
- **Strengths:** Lowest-latency multi-hop queries (p99 <140ms claims), thousands of tenant graphs per instance, #1 on GraphRAG-Bench with SDK 1.0 (Apr 2026), default engine for Graphiti MCP agent memory ([GraphRAG SDK 1.0](https://www.falkordb.com/blog/graphrag-sdk-knowledge-graph/), [openPR](https://www.openpr.com/news/4494136/falkordb-ships-graphrag-sdk-1-0-ranks-1-on-graphrag-bench), [Graphiti+FalkorDB](https://www.falkordb.com/blog/mcp-knowledge-graph-graphiti-falkordb/)). Excellent R8.
- **Fails/risks:** R1 — RAM-resident: billions of nodes/edges + TB payloads means a very expensive RAM cluster; no tiered storage. R3/R4 none. SSPL is workable for self-host but a license some orgs refuse.

### 5. Memgraph

- **Version/license:** **3.8 (Feb 2026)**; Community under **BSL 1.1** (converts to Apache 2.0 after 4 years per release); Enterprise proprietary, plus a separate "AI Platform" license tier for vector-heavy workloads ([3.8 release](https://memgraph.com/blog/memgraph-3-8-release-atomic-graphrag-vector-single-store-parallel-runtime), [BSL text](https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt)).
- **Strengths:** In-memory C++ engine, parallel runtime, single-store vector index (66–76% less RAM), atomic GraphRAG context queries, strong streaming/dynamic-algorithms story, good MCP tooling.
- **Fails/risks:** R1 — in-memory-first: billions of nodes = terabytes of RAM; the growth path is priced accordingly (community complaints about enterprise pricing: [HN thread](https://news.ycombinator.com/item?id=43813626)). R3/R4 none. Fine as a hot-cache/analytics companion, not the system of record for this project.

### 6. NebulaGraph

- **Version/status:** Enterprise **V5.2** (Nov 2025) — in-database compute engine, "100x faster path queries," graph-vector-text hybrid retrieval; open-source core (v3.x line, Apache 2.0) increasingly trails the enterprise line ([2025 year in review](https://www.nebula-graph.io/posts/NebulaGraph_2025_Year_in_Review), [GitHub releases](https://github.com/vesoft-inc/nebula/releases)).
- **Strengths:** Genuinely proven at hundred-billion-edge scale (Tencent, Meituan et al.); shared-nothing distributed; cheap-ish horizontal growth.
- **Fails/risks:** Heavy ops footprint (3 services + metad) — bad "start tiny" story (R1 start); open-core divergence risk (R9); no versioning/branching (R3/R4); Western community thinner than Neo4j's.

### 7. TigerGraph

- **Status:** ~30% layoffs, failed funding, pivot to Savanna managed cloud ([TrueUp](https://www.trueup.io/co/tigergraph/layoffs), [Savanna](https://www.tigergraph.com/savanna/)). Proprietary license, free tier limited.
- **Strengths:** Best-in-class deep-link analytics (10+ hop) at billions of edges; GSQL.
- **Verdict:** Fails R9 (proprietary, no clean self-host path) and now carries existential vendor risk. Eliminated despite excellent R2 fit.

### 8. Dgraph

- **Status:** Acquired by **Istari Digital** (Oct 2025) after the 2023 Hypermode acquisition; v25 made former enterprise features (namespaces, MCP server, v2 APIs) default; Apache 2.0 ([repo](https://github.com/hypermodeinc/dgraph), [gdotv recap](https://gdotv.com/blog/yearly-edge-graph-technology-news-recap-2025/)).
- **Strengths:** Distributed-native from day one, GraphQL API (good R8), horizontal write scaling (good R5).
- **Fails/risks:** Two ownership changes in two years; community trust damaged; DQL/GraphQL — no Cypher/GQL; no versioning/branching; single-machine start is fine but the project's long-term stewardship is the least predictable of the open-source options.

### 9. Amazon Neptune (Database + Analytics)

- **Status:** Mature managed service; cluster volume max **128 TiB**; serverless; Gremlin/openCypher/SPARQL ([limits doc](https://docs.aws.amazon.com/neptune/latest/userguide/limits.html)). **Neptune Analytics** is a separate in-memory graph+algorithms+vector engine billed in m-NCUs (now down to 32 m-NCU entry, pause at 10% cost; 7 new regions Feb 2026; Database Savings Plans Mar 2026) ([capacity units](https://aws.amazon.com/about-aws/whats-new/2024/07/amazon-neptune-analytics-smaller-capacity-units), [regions](https://aws.amazon.com/about-aws/whats-new/2026/02/amazon-neptune-analytics-in-seven-additional-regions), [pricing guide](https://www.usage.ai/blogs/aws/database-savings-plans/neptune-pricing/)).
- **Verdict:** Fails R9 outright (not self-hostable, lock-in, export friction) and R1's "start tiny/cheap" (always-on cluster billing). No branching/versioning. Eliminated as primary; noted as a managed escape hatch.

### 10. Google Spanner Graph (new since 2024)

- GA Jan 2025; ISO **GQL** + SQL interop; scales past trillions of edges; 2026 added in-GQL graph algorithms over tens of billions of edges ([announcement](https://cloud.google.com/blog/products/databases/announcing-spanner-graph), [algorithms](https://cloud.google.com/blog/products/databases/introducing-spanner-graph-algorithms), [overview](https://docs.cloud.google.com/spanner/docs/graph/overview)).
- **Verdict:** The best pure scale ceiling in the market, but managed-only GCP — fails R9. Relevant as proof that GQL-on-relational is where hyperscalers landed (validates the "relational store + graph query layer" architecture).

### 11. TerminusDB

- **Status:** Stewardship moved to **DFRNT** (2025); active; open source; document-graph with **native git-for-data**: branch, diff, merge, time-travel, immutable commit history, queryable branches without checkout ([terminusdb.org](https://terminusdb.org/), [version-control docs](https://terminusdb.org/docs/knowledge-graph-version-control/), [New Stack](https://thenewstack.io/terminusdb-takes-on-data-collaboration-with-a-git-like-approach/)).
- **Strengths:** The only engine that natively delivers R3 + R4 (branches are named pointers to commits; sub-second cross-branch WOQL/GraphQL queries; merge machinery built in). Schema-checked JSON documents fit "immutable facts."
- **Fails/risks:** R1 — no evidence of billions-of-nodes deployments; succinct-data-structure storage historically struggled with very large commits and heavy write concurrency (R5); small team/community; WOQL is niche (R8 partial via GraphQL). Best used as a design reference for the branching layer, or as the propose/review staging store — not the eventual system of record at target scale.

### 12. DuckDB + DuckPGQ

- **Status:** DuckPGQ is the CWI-built community extension implementing SQL:2023 **SQL/PGQ** property-graph queries over DuckDB tables; install is two commands; still "under active development," not core ([DuckDB docs](https://duckdb.org/docs/current/guides/sql_features/graph_queries), [duckpgq.org](https://duckpgq.org/), [VLDB paper](https://www.vldb.org/pvldb/vol16/p4034-wolde.pdf)).
- **Verdict:** Not a system of record (single-writer, extension maturity), but an outstanding **solver-side companion**: run path/reachability/pattern queries directly over Parquet snapshot exports. Pairs naturally with a Postgres or Ladybug store. Fails R3/R4/R5 as primary.

### 13. HelixDB (new, 2025–2026)

- Rust OLTP **graph+vector on object storage**; YC + NVIDIA backed ($500K — tiny); GA'd 2026; **AGPL-3.0**; v2 replaced its HelixQL DSL with a Rust DSL ([GitHub](https://github.com/HelixDB/helix-db), [Crunchbase](https://www.crunchbase.com/organization/helixdb), [dbdb.io](https://dbdb.io/db/helixdb)). Object-storage-native design is exactly the right R1 shape, but: AGPL, query-language churn mid-flight, near-zero production track record. Watch list, not shortlist.

### 14. ArcadeDB

- Apache 2.0 multi-model (graph/document/KV/vector/time-series), JVM, embedded-or-server-or-HA-Raft, speaks Cypher + Gremlin + SQL + MongoDB API; **v26.3.1** added MCP server and AI assistant; aggressive self-published benchmarks (LDBC Graphalytics wins, LSQB Q6 1.67B-row two-hop in 110ms) ([arcadedb.com](https://arcadedb.com/), [benchmarks](https://arcadedb.com/benchmarks.html), [Neo4j-alternatives post](https://arcadedb.com/blog/neo4j-alternatives-in-2026-a-fair-look-at-the-open-source-options/)). Credible permissive-license dark horse (it published Kuzu migration guides and picked up refugees), but small single-vendor community and vendor-published benchmarks warrant skepticism. No versioning/branching.

### 15. Others considered and set aside

- **Apache AGE standalone** — covered under Postgres; not a standalone engine.
- **JanusGraph/OrientDB/HugeGraph** — legacy-mode maintenance; no momentum ([Solutions Review roundup](https://solutionsreview.com/data-management/the-best-graph-databases/)).
- **Ultipa, GraphLite** — early GQL-compliant engines worth watching for the standard, not for this workload ([gdotv recap](https://gdotv.com/blog/yearly-edge-graph-technology-news-recap-2025/)).
- **PuppyGraph** — zero-ETL graph query layer over lakehouse tables; interesting future read-layer pattern, not a store ([puppygraph.com](https://www.puppygraph.com/blog/best-graph-databases)).
- **Grafeo / OverGraph / Samyama** — new Rust engines, pre-production maturity ([Grafeo](https://grafeo.dev/), [OverGraph](https://github.com/bhensley5/overgraph)).
- **Graphiti (Zep)** — not an engine; temporal knowledge-graph *framework* over Neo4j/FalkorDB. Its bi-temporal edge model (valid-time + ingest-time, invalidation instead of deletion) is directly relevant prior art for R3's app-layer design ([GitHub](https://github.com/getzep/graphiti)).
- **Microsoft Fabric Graph** — new GQL surface in Fabric; managed-only ([docs](https://learn.microsoft.com/en-us/fabric/graph/gql-language-guide)).

---

## Requirement scorecard

✔ = good, ~ = workable/DIY, ✘ = fails

| Engine | R1 scale-path | R2 traversal/extract | R3 versioning | R4 branching | R5 parallel writes | R6 vector | R7 indexes | R8 MCP/API | R9 license/export |
|---|---|---|---|---|---|---|---|---|---|
| Postgres (+pgvector/AGE) | ✔ start / ~ ceiling | ~ (solver does deep hops) | ~ (easy DIY) | ~ (easy DIY) | ✔ | ✔ (pgvector) | ✔ | ✔ | ✔ |
| Neo4j | ~ start / ✔ ceiling ($$$) | ✔ | ✘ (DIY) | ✘ (DIY) | ~ | ✔ | ✔ | ✔ | ~ (CE GPLv3; scale features proprietary) |
| LadybugDB | ✔ start / ~ ceiling | ✔ (Arrow zero-copy) | ~ (Icebug snapshots) | ~ (potential) | ✘ (embedded) | ✔ (inherited) | ✔ | ~ | ✔ (MIT) — project risk |
| FalkorDB | ✘ (RAM-bound) | ✔ | ✘ | ✘ | ~ | ✔ | ~ | ✔ | ~ (SSPL) |
| Memgraph | ✘ (RAM-bound $$) | ✔ | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ | ~ (BSL) |
| NebulaGraph | ✘ start / ✔ ceiling | ✔ | ✘ | ✘ | ✔ | ~ (ent.) | ✔ | ~ | ~ (open-core drift) |
| TigerGraph | ✘ start | ✔ | ✘ | ✘ | ✔ | ✔ | ✔ | ~ | ✘ + vendor risk |
| Dgraph | ~ | ✔ | ✘ | ✘ | ✔ | ✔ | ✔ | ✔ (GraphQL/MCP) | ✔ license / ~ stewardship |
| Neptune (+Analytics) | ✘ (cost start) | ✔ | ✘ | ✘ | ✔ | ✔ | ✔ | ~ | ✘ |
| Spanner Graph | ✘ (managed) | ✔ | ✘ | ✘ | ✔ | ✔ | ✔ | ~ | ✘ |
| TerminusDB | ✘ ceiling | ~ | ✔ native | ✔ native | ~ | ~ | ✔ | ~ | ✔ |
| ArcadeDB | ✔ start / ~ ceiling | ✔ (claimed) | ✘ | ✘ | ~ | ✔ | ✔ | ✔ (MCP) | ✔ |
| DuckDB+DuckPGQ | ✔ start (read-side) | ✔ (analytics) | ✘ | ✘ | ✘ | ~ | ✔ | ~ | ✔ |
| HelixDB | ~ (object storage) | ~ | ✘ | ✘ | ~ | ✔ | ~ | ✔ | ~ (AGPL, immature) |

---

## Ranked shortlist

### 1. PostgreSQL as system of record (pgvector; AGE/SQL-PGQ optional; partitioned edge tables)

The requirements that eliminate most graph engines here are not the graph requirements — they are R3/R4/R5/R9. No scalable property-graph engine ships immutable per-entity history or git-like branching, so that layer is application-level regardless; Postgres is where building it is cheapest, most transactional, and most durable (append-only fact tables, branch-delta tables, `ON CONFLICT` commutative merges). It starts at $0 on one machine, its MVCC handles swarms of parallel agent writers better than any single-leader graph DB, pgvector covers R6 to a very large scale with a clean sidecar path beyond, and the 8-edge-type pruning requirement maps *exactly* onto native list partitioning. Its genuine weakness — deep recursive traversal over huge fan-outs — is precisely the thing the ADR already moves into an in-memory solver; the engine's job is cheap fat subgraph reads, which is a Postgres strength. The hyperscalers' 2025–2026 moves (Spanner Graph, Fabric GQL, SQL/PGQ in SQL:2023) all validate graph-on-relational. Clean export (SQL/Parquet) keeps the engine swappable per R9.

### 2. Neo4j (Community now, Enterprise/Infinigraph if the graph earns it)

The strongest graph-native counterargument: unmatched ecosystem, first-class Cypher/GDS/MCP/LLM tooling, GA vector index, and the only self-hostable engine with *proven* trillion-relationship, 100TB+ scale (Infinigraph, Sept 2025). If the project wants graph ergonomics from day one and accepts DIY versioning/branching, Neo4j CE on one box is a fine start. The reasons it's #2: the growth path runs through a steep commercial cliff (CE is single-instance GPLv3; sharding/scale/GDS are paid), write throughput is single-leader, and R3/R4 are just as DIY as on Postgres but on a costlier substrate. Best kept as the "graduate to it" option — the data model should be designed so a Postgres→Neo4j (or →GQL engine) migration is mechanical.

### 3. LadybugDB (Kuzu successor) as embedded solver-side engine — and possible early primary

The Kuzu lineage is almost purpose-built for R2: embedded, columnar, vectorized Cypher with factorized execution, Arrow zero-copy handoff straight into an in-memory solver, vector + FTS included, MIT-licensed, runs anywhere for free. The fork is alive and shipping (v0.17.0, May 2026), and its Icebug/Iceberg-style snapshot format plus object-store "graph lakehouse" direction is the most promising storage-level substrate for cheap R3/R4 of any graph-native engine. What keeps it at #3: it's a months-old community fork of an abandoned project with no funding — exactly the scenario R9's swappability clause exists for — and its embedded single-writer model can't host the parallel agent-swarm write path (R5). Recommended role: the traversal/analytics engine fed by Parquet exports from the system of record, with a promotion path if the project matures.

### 4. FalkorDB as the agent-facing hot layer (niche), with TerminusDB as the R3/R4 design reference

FalkorDB is the best-in-class low-latency GraphRAG/agent-memory serving layer in 2026 (GraphBLAS sparse-matrix engine, #1 on GraphRAG-Bench, default Graphiti MCP backend) and would slot in cleanly as a hot cache for agent subgraph reads (R8) — but its all-in-RAM architecture disqualifies it as the billion-node system of record (R1), and SSPL narrows options. TerminusDB deserves the honorable mention from the other direction: it is the *only* engine with native git-for-data branch/diff/merge/time-travel, and even if its scale ceiling rules it out as primary, its commit-graph design (and Graphiti's bi-temporal edge model) should directly inform the branching/versioning layer built on whichever engine wins.

**Bottom-line recommended architecture:** Postgres system-of-record (append-only facts, branch tables, pgvector, 8-way edge-type partitions) → Parquet/Arrow snapshot exports → LadybugDB/DuckPGQ for deep traversal + solver feeds → optional FalkorDB hot layer for agent MCP reads. Every seam is an open format, satisfying R9's engine-swap mandate.
