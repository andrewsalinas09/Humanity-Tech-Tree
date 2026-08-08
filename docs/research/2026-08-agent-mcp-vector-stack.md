# LLM-Agent + MCP + Semantic-Search Stack — Research Snapshot (August 2026)

Research for the Humanity Tech Tree: a knowledge graph authored primarily by parallel LLM agent
swarms via MCP tools, with humans as verifiers. Every node gets an embedding at creation;
"does this node already exist?" must answer in seconds against (eventually) billions of nodes.

All findings below are from web research performed 2026-08-08. URLs cited inline.

---

## A) MCP + Graph/DB Tooling Maturity

### A.1 Protocol state: the 2026-07-28 spec is a major inflection point

The MCP spec's **2026-07-28 release candidate** is the largest revision since launch
([modelcontextprotocol.io blog](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/),
[4sysops summary](https://4sysops.com/archives/2026-07-28-model-context-protocol-mcp-stateless-multi-round-trip-routable-headers-authorization-hardening/),
[mcpservers.org analysis](https://blog.mcpservers.org/posts/mcp-spec-2026-07-28)). Directly relevant to us:

- **Stateless core** that scales on ordinary HTTP infrastructure (load balancers, auto-scaling) —
  exactly what a swarm of hundreds of agents needs; no sticky sessions.
- **Full JSON Schema 2020-12** for tool `inputSchema` *and* `outputSchema` (composition via
  `oneOf`/`anyOf`, `$ref`/`$defs`); `structuredContent` in results can now be any JSON value.
  This makes **machine-readable rejections** first-class: a `create_node` tool can return a typed
  `{"status": "rejected", "reason": "duplicate", "existing_node_id": ..., "similarity": ...}` payload
  that agents can branch on deterministically.
- **Error convention codified**: tool-execution failures go *inside* the result as
  `isError: true` + message (not JSON-RPC protocol errors); protocol errors use standard JSON-RPC
  codes ([spec timeline](https://hidekazu-konishi.com/entry/mcp_specification_version_timeline.html),
  [changelog roundup](https://tokenmix.ai/blog/mcp-updates-changelog-every-protocol-change-2026)).
- **Tasks extension** for long-running work (e.g., bulk imports, re-embedding jobs) and a formal
  deprecation policy.

**Implication:** design our MCP tool contracts against the 2026-07-28 RC — structured output
schemas for every write tool, with rejections as data, not prose.

### A.2 Graph-DB MCP servers that exist today

- **Neo4j (official, `neo4j/mcp`)** — the reference implementation
  ([GitHub](https://github.com/neo4j/mcp), [docs](https://neo4j.com/docs/mcp/current/),
  [ecosystem page](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)).
  Four tools: `get-schema`, `read-cypher` (read-only enforced via `EXPLAIN`), `write-cypher`
  (can be globally disabled via `NEO4J_READ_ONLY=true`), `list-gds-procedures`. PyPI:
  `neo4j-mcp-server`. There's also the older Neo4j Labs collection
  ([neo4j-contrib/mcp-neo4j](https://github.com/neo4j-contrib/mcp-neo4j)) with memory/Aura variants,
  and a [GraphAcademy course](https://graphacademy.neo4j.com/courses/genai-mcp-neo4j-tools) on
  building with the tools. Servers support HTTP transport for scalable production deployments.
- **Memgraph** — actively advancing its MCP server with modular architecture, vector-search tools,
  and Memgraph Lab acting as an MCP client ([Memgraph blog/AI](https://memgraph.com/blog/categories/ai)).
- **FalkorDB** — positions itself for GraphRAG/multi-tenant agent use: native vector indexing,
  GraphRAG-SDK, claimed 10K+ tenant graphs ([falkordb.com](https://www.falkordb.com/)). A
  multi-backend MCP knowledge-graph server supports FalkorDB (default), Neo4j, Kuzu, and Amazon
  Neptune ([ChatForest roundup](https://chatforest.com/guides/best-memory-mcp-servers/)).
- **Kuzu** — caution: the Kuzu repo was **archived October 2025** and is no longer maintained
  ([ArcadeDB comparison](https://arcadedb.com/blog/neo4j-alternatives-in-2026-a-fair-look-at-the-open-source-options/)).
  Community MCP servers exist ([glama.ai listing](https://glama.ai/mcp/servers/jordanburke/kuzudb-mcp-server))
  but don't build on it.

**Key observation:** all mainstream graph MCP servers are essentially *"run Cypher for me"*
wrappers. Nobody ships a production-grade *domain-tool* server (typed `propose_node`,
`link_nodes`, `search_similar` with dedup gating). For an agent-authored graph, raw-Cypher
tools are the wrong abstraction — the established guidance is to design tools around
task-shaped verbs with tight schemas ([MCP tool schema design guide](https://kansei-link.com/en/insights/mcp-tool-schema-design-guide-2026.html),
[enterprise MCP patterns](https://www.digitalapplied.com/blog/mcp-server-patterns-enterprise-ai-agents)).
We should build our own thin MCP server over the DB; existing servers are useful for
human/ad-hoc exploration only.

### A.3 Production patterns for agent swarms writing through MCP

From 2026 production literature
([Peliqan rate-limit guide](https://peliqan.io/blog/mcp-rate-limits-guide/),
[Fastio implementation guide](https://fast.io/resources/mcp-server-rate-limiting/),
[MintMCP](https://www.mintmcp.com/blog/rate-limiting-with-mcp),
[MintMCP gateways](https://www.mintmcp.com/blog/mcp-gateways-rate-limiting-access-control),
[production-grade agents guide](https://dev.to/thedailyagent/building-production-grade-ai-agents-with-mcp-a-complete-guide-for-2026-3bo2)):

- **Rate limits are the #1 production failure mode** for MCP agents in 2026. Agentic loops now
  average 8–15 tool calls per turn (vs 2–3 in 2024), and SaaS vendors tightened limits
  specifically to slow agent traffic.
- **Never retry inside the agent's turn.** Bubble the 429/rejection back to the model with a
  clear, structured error; cascading in-turn retries are the top cause of MCP outages. A
  misbehaving agent in a retry loop can exhaust connections for the whole swarm — per-agent
  rate limiting isolates the damage.
- **Separate bulk and interactive paths**: bulk ingestion must never share a queue/budget with
  interactive tool calls (separate workers, separate budgets).
- **Gateway topologies** are established: single-tenant, multi-tenant row-isolated, federated
  gateway (central audit), and edge-cached read-only. A federated gateway with central audit
  fits a community-verified graph well.
- **System of record lives in the database, not in agent message history** — teams that put
  authority in the DB (transactional, audit-friendly, vector-indexed) fare best
  ([Oracle agent-communication matrix](https://blogs.oracle.com/developers/the-agent-communication-matrix-when-mcp-a2a-and-plain-rest-each-win)).
- **Concurrent-write consistency** is a documented failure mode: test with a small swarm (3–5
  agents) before scaling; watch for agents producing contradictory writes to shared state, which
  typically needs a synthesis/reconciliation step
  ([multi-agent orchestration patterns](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work),
  [CoAgent: concurrency control for multi-agent systems](https://arxiv.org/pdf/2606.15376),
  [MCP agent communication survey](https://arxiv.org/pdf/2506.05364)).
- Tools vs resources discipline: tools are verbs (state-changing), resources are nouns
  (read-only context). Keep reads cheap and cacheable; make writes explicit and audited.

**Idempotency pattern for us:** every write tool takes a client-supplied idempotency key
(or is naturally idempotent via content-hash of the canonical node payload), so a retried
agent call can't double-create. Combine with the structured-rejection payload from A.1 so a
"duplicate detected" outcome is a *successful* tool result carrying the existing node's ID —
the agent's correct next move is encoded in the response, not left to interpretation.

---

## B) Embedding / ANN at Billion Scale

### B.1 The landscape: who is actually "billion-serious" in 2026

Consensus across 2026 comparisons
([Firecrawl guide](https://www.firecrawl.dev/blog/best-vector-databases),
[digitalapplied 8-DB comparison](https://www.digitalapplied.com/blog/vector-databases-for-ai-agents-pinecone-qdrant-2026),
[EFFOMA systematic analysis](https://effoma.com/blog/vector-database-performance-benchmark-comparison-2026/),
[Mixpeek cost comparison](https://mixpeek.com/guides/vector-database-cost-comparison)):

| Option | Billion-scale verdict (2026) |
|---|---|
| **Milvus / Zilliz** | Architecturally designed for 1B+; DiskANN native since 2.5; RaBitQ 1-bit quantization in 2.6 compresses indexes to 1/32 size at ~95% recall. Ops-heavy: budget 0.5–1 FTE SRE self-hosted. Avoid below ~100M vectors — overhead not worth it. |
| **Vespa** | The other "billion-vector serious" option; a decade of Yahoo-scale production; dense+sparse+structured with programmable ranking; harder to operate. |
| **Turbopuffer** | Object-storage-first (S3/GCS + NVMe cache + RAM cache); proven at extreme scale: Cursor indexes 1T+ code chunks across 80M+ namespaces; Notion migrated 10B+ vectors. Usage pricing: storage ~$0.02/GB-month, scan rate cut 5x to $1/PB in Feb 2026; minimums $64/$256/$4,096 monthly. ~$100M ARR (Sacra, Mar 2026) — commercially healthy. ([turbopuffer.com](https://turbopuffer.com/), [Sacra](https://sacra.com/c/turbopuffer/), [architecture writeup](https://jxnl.co/writing/2025/09/11/turbopuffer-object-storage-first-vector-database-architecture/)) |
| **Qdrant** | Excellent to hundreds of millions with quantization; strong payload filtering; documented 500M deployment with INT8 quantization at $8,200/mo, 97.8% recall (vs $30,200 all-RAM). Managed 1B estimates range $1.8K–$19K/mo depending on tier/QPS. ([Spheron self-hosting guide](https://www.spheron.network/blog/self-host-vector-database-gpu-cloud-qdrant-milvus-weaviate/), [ranksquire pricing](https://ranksquire.com/2026/03/04/vector-database-pricing-comparison-2026/)) |
| **pgvector + pgvectorscale** | StreamingDiskANN + statistical binary quantization; beats Pinecone s1 by 28x p95 latency at 99% recall on 50M/768d at 75% less cost ([TigerData](https://www.tigerdata.com/blog/pgvector-is-now-as-fast-as-pinecone-at-75-less-cost)). But 2026 guidance caps its sweet spot at **10M–50M vectors** ([2026 production guide](https://devstarsj.github.io/2026/04/04/postgresql-pgvector-pgvectorscale-rag-production-guide-2026/), [Postgres stack comparison](https://www.web3aiblog.com/blog/postgres-vector-search-compared-pgvector-pgvectorscale-paradedb-lantern-2026)). |
| **LanceDB / Weaviate** | Fine mid-scale; not cited as first-choice at 1B in the 2026 comparisons reviewed. |

Hardware reality at 1B ([Spheron](https://www.spheron.network/blog/self-host-vector-database-gpu-cloud-qdrant-milvus-weaviate/)):
1B × 1536d float32 ≈ **6 TB raw**; Milvus+DiskANN needs ~60–120 GB memory for graph overhead;
in-memory/GPU indexes are impractical at this scale — quantization + SSD/object-storage tiering
is mandatory. Billion-scale cost bands: roughly $500–$5,000+/mo depending on throughput,
redundancy, managed vs self-hosted ([Mixpeek](https://mixpeek.com/guides/vector-database-cost-comparison)).

**Recommendation for Humanity Tech Tree:**
- **Start**: pgvector(+pgvectorscale) inside the primary Postgres, or Qdrant, while the graph is
  <10M nodes. Keeping embeddings next to the graph rows early simplifies transactional
  "create node + embed + dedup-check" writes.
- **Scale path**: Turbopuffer is the standout cost/scale story for an entity-dedup workload
  (mostly-cold data, spiky agent-driven queries, per-namespace isolation) *if* managed is
  acceptable; Milvus (or Vespa) if self-hosting/sovereignty is required.
- Crucial mitigator: **our vectors are short entity descriptions** — at 256–512d (see B.2),
  1B vectors is ~1–2 TB before quantization, ~10x cheaper than the 1536d scenarios above.

### B.2 Embedding model choice for short entity descriptions

2026 guidance ([pecollective specs table](https://pecollective.com/tools/text-embedding-models-compared/),
[link.sc comparison](https://link.sc/blog/best-embedding-models-2026),
[BentoML open-source guide](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models),
[tensoria benchmark](https://tensoria.fr/en/blog/embedding-models-2026-guide)):

- Practical sweet spot for retrieval is **768–1024d**; nearly every 2026-era model supports
  **Matryoshka representation learning (MRL)**, so you can truncate 3072d→1024/512d with minor
  quality loss.
- Cheap workhorse: OpenAI `text-embedding-3-small` at $0.02/1M tokens covers ~95% of
  general-purpose English retrieval; Cohere embed-v4 is the enterprise pick (MRL dims, VPC).
  Open-source (BGE/GTE/Qwen-embedding families) removes per-token cost entirely — attractive
  when agent swarms embed every candidate node.
- **Established recipe**: embed at full dimension, **store a truncated 256–512d copy for
  first-stage ANN, rerank top-K with full vectors**. This directly fits the dedup-gate design:
  fast coarse candidate generation, precise confirmation.
- Short entity descriptions are cheap to embed (tens of tokens each) — even 1B nodes ≈ tens of
  billions of tokens ≈ low-thousands of dollars at API pricing, or near-free self-hosted.
  Embedding cost is *not* the bottleneck; re-embedding logistics are (B.3).

### B.3 Re-embedding strategy when models improve

Critical constraint: **embedding spaces are incompatible across models** — you cannot mix old
vectors with new queries; there is no safe "normalization," only silent retrieval drift
([hidden cost of model upgrades](https://medium.com/data-science-collective/different-embedding-models-different-spaces-the-hidden-cost-of-model-upgrades-899db24ad233),
[version-drift explainer](https://aboutvectordatabase.com/learn/handling-updates-to-embedding-model-version-drift/)).
Established 2026 patterns
([zero-downtime migration, GCP](https://medium.com/google-cloud/migrating-vector-embeddings-in-production-without-downtime-8a0464af6f55),
[embedding versioning & index drift](https://tianpan.co/blog/2026-04-09-embedding-models-production-versioning-index-drift)):

1. **Dual-column / parallel index**: add a second vector column (or index), backfill in the
   background, keep serving from the old one.
2. **Alias swap**: validate the new index against a golden query set, then atomically swap the
   alias; instant rollback by swapping back.
3. **Lazy re-embed** with a harmonization adapter for the mixed period —
   [Drift-Adapter (arXiv 2509.23471)](https://arxiv.org/pdf/2509.23471) trains a small transform
   for near-zero-downtime upgrades.
4. Treat the vector store **like a cache over canonical text** ([HackerNoon](https://hackernoon.com/why-your-vector-database-should-be-treated-like-a-cache)) —
   the durable asset is the node's canonical description; vectors are derived, versioned artifacts.

**Design consequences for us**: store `embedding_model_version` on every node; keep canonical
text authoritative; build the golden-query eval set *early* (it's the gate for every future
migration); budget periodic full re-embeds as routine ops, not emergencies.

### B.4 Dedup / entity-resolution: ANN candidates + LLM judgment

This is now an established pattern with published numbers:

- **Three-tier gate** ([Elastic Labs](https://www.elastic.co/search-labs/blog/elasticsearch-entity-resolution-llm-semantic-search),
  [Towards AI: GPT-4o-mini as ER judge](https://pub.towardsai.net/using-gpt-4o-mini-as-an-entity-resolution-judge-95-precision-for-0-04-b216d44a7f20)):
  auto-accept similarity ≥ 0.95, **LLM judge for 0.75–0.95**, auto-reject < 0.75. Reported:
  ANN blocking alone (MiniLM, top-20) = 35.5% precision / 59.4% recall; adding a GPT-4o-mini
  judge = **95.4% precision** / 50.9% recall, at ~$0.04 per dataset run. Precision jumps hugely;
  recall is bounded by candidate generation — invest in the blocking stage (multiple signals,
  aliases, higher K).
- **Multi-signal matching** (embeddings + fuzzy string + structured attributes) outperforms
  vectors alone ([multi-signal system writeup](https://medium.com/@akulkarni5208/ai-powered-entity-matching-how-i-built-a-multi-signal-matching-system-using-llm-embeddings-and-763c039220da),
  [Modern Data 101 on ER at scale](https://www.moderndata101.com/blogs/entity-resolution-at-scale-deduplication-strategies-for-knowledge-graph-construction)).
- **Active-learning loop**: uncertain pairs surface for human review, prioritized by expected
  value of judgment ([self-serve ER pipeline lessons, arXiv 2607.26298](https://arxiv.org/html/2607.26298v1)) —
  this maps exactly onto our humans-as-verifiers role.
- Research caveats: LLM matchers vary by prompt formulation ("Match, Compare, or Select?",
  [arXiv 2405.16884](https://arxiv.org/pdf/2405.16884)) and **LLM self-explanations for ER
  decisions are not reliably faithful** ([arXiv 2606.01210](https://arxiv.org/pdf/2606.01210)) —
  log the evidence (scores, matched fields), don't trust the judge's prose rationale.
- Open-source implementations are converging on the same design (e.g.,
  [cognee's LLM-judge canonicalization work](https://github.com/topoteretes/cognee/issues/3629)).

**For our "does this node exist?" gate**: MRL-truncated ANN (top-50, coarse) → full-vector +
lexical/alias rerank → threshold tiers → LLM judge on the borderline band → human verifier queue
for judge-uncertain cases. Return the verdict as structured MCP output (A.1/A.3).

---

## C) GraphRAG / LLM-Built Knowledge Graphs — State of the Art

### C.1 The Microsoft GraphRAG lineage

- Original GraphRAG (2024) cost ~$33K to index large corpora; successors — **LazyGraphRAG,
  LightRAG, Fast GraphRAG** — cut indexing cost 50–6,000x with equal or better global-question
  accuracy ([CallSphere overview](https://callsphere.ai/blog/vw6g-microsoft-graphrag-knowledge-graph-2026),
  ["The GraphRAG Cost Cliff"](https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4)).
- **LazyGraphRAG** ([Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)):
  defers LLM work to query time; won all 96 head-to-head comparisons vs alternatives incl. a
  1M-token context window; indexing nearly free. Shipping via Microsoft Discovery/Azure, with
  open-source library integration landing across 2026
  ([articsledge](https://www.articsledge.com/post/lazygraphrag-retrieval-augmented-generation)).
  Microsoft also released **BenchmarkQED** for automated RAG benchmarking
  ([MSR blog](https://www.microsoft.com/en-us/research/blog/benchmarkqed-automated-benchmarking-of-rag-systems/)).
- Static GraphRAG's documented weakness: **frequently-changing data forces extensive
  recomputation** — a direct caution for a continuously-authored tech tree. The field's answer
  is incremental/temporal graphs (below).

### C.2 Agentic & incremental KG construction (the 2026 frontier)

- **Agentic GraphRAG** is a named paradigm now: the agent plans/acts/critiques over graph
  operations — the graph is the space the agent moves through, not a passive lookup
  ([SSRN survey of Agentic GraphRAG](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6713979)).
- **Graphiti/Zep**: temporally-aware KG engine; every fact carries a validity window;
  contradictions *invalidate* old edges rather than delete them (audit-preserving);
  LLM-based entity resolution on ingest; 63.8% vs 49.0% (Mem0) on LongMemEval
  ([Neo4j blog](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/),
  [Zep paper, arXiv 2501.13956](https://arxiv.org/abs/2501.13956),
  [Graphiti guide](https://medium.com/@saeedhajebi/building-ai-agents-with-knowledge-graph-memory-a-comprehensive-guide-to-graphiti-3b77e6084dec)).
  The bi-temporal edge model (fact validity + record time) is directly reusable for a tech tree
  where historical claims get revised.
- **AutoSchemaKG / ATLAS** ([arXiv 2505.23628](https://arxiv.org/abs/2505.23628),
  [ACL 2026](https://aclanthology.org/2026.acl-long.942/)): fully autonomous KG construction
  with *dynamic schema induction* — 50M documents → **900M+ nodes, 5.9B edges**; induced schema
  reaches 92% semantic alignment with human-crafted schemas; +12–18% on multi-hop QA. Proof that
  billion-node LLM-built graphs are feasible — and a benchmark for what "no fixed ontology"
  looks like.
- **AutoGraph-R1** ([arXiv 2510.15339](https://arxiv.org/pdf/2510.15339)): end-to-end RL for KG
  construction — optimizing extraction against downstream task reward rather than triple F1.
- Surveys: [LLM-empowered KG construction survey (arXiv 2510.20345)](https://arxiv.org/html/2510.20345v1);
  ontology-grounded construction under the Wikidata schema
  ([arXiv 2412.20942](https://arxiv.org/pdf/2412.20942)).
- Ecosystem datapoint: a May 2026 MLOps Community benchmark across 47 production deployments
  found agentic pipelines paired with KGs cut hallucination rates ~62% vs naive RAG; most 2026
  production stacks are **hybrid vector+graph, routed by query type**
  ([CallSphere](https://callsphere.ai/blog/vw6g-microsoft-graphrag-knowledge-graph-2026)).

### C.3 Documented failure modes (all directly relevant to us)

From practitioner postmortems and papers
([Atlan KG-construction guide](https://atlan.com/know/ai-agent/knowledge-graph/knowledge-graph-construction-for-ai/),
["Why I stopped letting LLMs build my knowledge graphs"](https://medium.com/@balaaditya_25928/why-i-stopped-letting-llms-build-my-knowledge-graphs-and-what-i-did-instead-263e7b8e7ab6),
[industrial-asset KG paper](https://arxiv.org/html/2605.26874)):

1. **Hallucinated edges**: LLMs infer plausible-but-false relationships; unconstrained
   extraction *requires* a downstream validation layer. Failures are often data-access
   failures dressed as reasoning (fabricated identifiers, miscounted cross-document facts).
2. **Duplicate entities**: canonical horror story — one service (`PaymentService`) appearing as
   **five separate nodes**; and naive pipelines re-process the whole graph on every addition,
   with LLM-call costs climbing. Consensus: most enterprise KG builds **stall at entity
   resolution and ontology alignment, not extraction**.
3. **Plausibility trap**: LLM output *looks* valid, so teams skip structural validation.
   Consensus rule: **all LLM output is candidate-only until it passes a validation gate.**
4. **Ontology drift**: mitigations are either a designed ontology up front (Atlan's 5-stage
   pipeline: scope → ontology → extract → resolve to golden record → validate/activate) or
   deliberate schema induction with measured alignment (AutoSchemaKG's 92%).
5. **Hallucination detection via graph alignment** is an active area:
   [HalluGraph](https://arxiv.org/pdf/2512.01659) (auditable KG-alignment checks),
   [KGValidator](https://arxiv.org/pdf/2404.15923) (automatic validation of KG construction),
   [traceable LLM validation of KG statements](https://arxiv.org/pdf/2409.07507) (citation-grounded
   statement checking — directly applicable to a citable graph).

### C.4 Community-verified graph precedents (Wikidata)

Wikidata is the best living precedent for "agents write, community verifies"
([Human-Bot collaboration analysis](https://arxiv.org/pdf/1810.00931),
[agreement/disagreement in collaborative KG construction](https://arxiv.org/pdf/2306.11766)):

- ~24K active human editors, ~100 active bots/month; **bots perform 52% of all edits**.
- Governance that scales: bots require a **Request for Permission** with a described scope and a
  supervised **test run of 50–250 edits** voted on by the community before activation. This maps
  cleanly onto agent-swarm onboarding: new agent version → sandboxed probation batch → human
  sign-off → production write access.
- Edit history itself is a refinement signal ([leveraging Wikidata's edit history](https://arxiv.org/pdf/2210.15495));
  LLM participation in knowledge communities is being actively studied
  ([arXiv 2509.07819](https://arxiv.org/pdf/2509.07819)), with provenance/transparency the top
  concerns ([Wikidata Workshop](https://wikidataworkshop.github.io/2025/)).

---

## Consolidated Recommendations for Humanity Tech Tree

1. **Build a custom, task-shaped MCP server** (propose_node / search_similar / link_nodes /
   propose_merge), stateless HTTP per the 2026-07-28 spec, with JSON-Schema'd structured outputs
   where "duplicate found" is a successful, machine-readable result carrying the existing node ID.
   Idempotency keys (or content-hash identity) on all writes. No raw-Cypher write tool for agents.
2. **Gateway in front**: per-agent rate limits and budgets, separate bulk vs interactive queues,
   central audit log; never auto-retry inside a turn.
3. **Vectors**: MRL-capable embedding model; store 256–512d truncated vectors for the fast dedup
   gate + full vectors for rerank; `embedding_model_version` on every node; canonical text is the
   durable asset; golden-query eval set from day one. Start on pgvector/Qdrant; plan the 100M+
   jump to Turbopuffer (managed, object-storage economics) or Milvus/Vespa (self-hosted).
4. **Dedup gate** = tiered: ANN top-K → multi-signal rerank → auto-accept/auto-reject thresholds →
   LLM judge on the borderline band (expect ~95% precision there) → human-verifier queue for
   uncertain pairs. Log evidence, not judge prose.
5. **Graph semantics**: adopt Graphiti-style bi-temporal edges (validity window + record time);
   invalidate, never delete; every edge carries provenance/citations, validated in the spirit of
   KGValidator/traceable-statement checking.
6. **Governance**: Wikidata's bot-permission model — agent versions earn write access through a
   supervised probation batch reviewed by humans; treat all agent output as candidate-only until
   it passes the validation gate.

## Biggest Cautionary Findings

- **Entity resolution, not extraction, is where LLM-KG projects die.** Plan for it as the core
  system, not a cleanup step.
- **Recall of the dedup gate is bounded by candidate generation** (LLM judges fix precision, not
  recall) — under-blocking silently accumulates duplicates at swarm speed.
- **Embedding-model migrations are whole-corpus events** with no shortcut; without versioning and
  an eval set, an upgrade silently corrupts the dedup gate.
- **Rate-limit/retry storms are the #1 MCP production outage cause**; a billion-node graph fed by
  swarms without per-agent budgets and structured backpressure will hit this early.
- **The plausibility trap**: hallucinated edges pass eyeball review. A citable graph needs
  citation-grounded validation on every claim, or verification debt compounds invisibly.
- **Ecosystem churn**: Kuzu was archived (Oct 2025) months after being widely recommended —
  prefer boring, revenue-backed infrastructure (Postgres, Neo4j, Milvus, Vespa, Turbopuffer)
  for anything hard to migrate.
