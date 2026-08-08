# Versioned / Branching / Immutable Data Stores — 2026 Landscape Survey

**Date:** 2026-08-08
**For:** Humanity Tech Tree storage-layer decision
**Method:** Live web research (August 2026), not training-data memory. URLs cited inline.

---

## 0. Executive summary

- **Native "git-for-data" at graph granularity exists and is healthier in 2026 than it was in 2023-24**, but the field is thin: **TerminusDB** (now stewarded by DFRNT), **Dolt/DoltgreSQL** (SQL, not graph), and — the notable new 2026 entrant — **FlureeDB** (RDF knowledge graph with branch/merge, immutable content-addressed commit chain, GA June 2026).
- **The systems that actually run citable-fact knowledge bases at planetary scale (Wikidata, OpenStreetMap) do NOT use storage-level branching.** Both use app-level change objects (revisions / changesets) over a plain store, with review, revert, and vandalism-audit tooling built above. This is strong precedent for the project's ChangeRequest design.
- **Bitemporality (XTDB/Datomic) solves transaction-time versioning beautifully but is the wrong tool for the project's *historical* time axis.** Fuzzy historical dates (decimal years ± uncertainty) must be ordinary domain data, not the database's valid-time column. XTDB/Datomic also lack branches — they have one immutable timeline.
- **CRDTs are not the right merge substrate for a review-gated graph.** The review/approve step is inherently an arbitration (non-commutative) step; what the project actually needs is *commutative application of approved change-sets*, which is an application-schema property (set-union semantics, LWW-per-field with provenance), not a CRDT library.
- **Recommendation (detailed in §6):** build **app-level ChangeRequests on a plain, boring, append-only store** (Postgres event-log/entity-version schema first), with the door explicitly held open to FlureeDB or TerminusDB as a later materialization/storage engine. Native branching DBs are worth a prototype spike, but none of them should own the system of record on day one, for reasons of project-risk (TerminusDB/Fluree stewardship & license), scale ceiling (Dolt memory profile), and model mismatch (XTDB/Datomic: no branches).

---

## 1. Requirements recap (what the store must satisfy)

From the project's laws:

| Law | Storage implication |
|---|---|
| Store holds only ground facts; everything else computed | Store can be simple; no need for in-DB inference/reasoning |
| No deletion ever; merge-redirects + lifecycle status | Append-only / immutable history; tombstone-free model |
| Full version history per entity | Per-entity revision chain, cheap to read |
| Git-like shadow branches, merged after review | Branch/isolate/diff/merge — native or app-level |
| Atomic rollback of graph sections | Grouped changes (changesets) revertible as a unit |
| "Patient zero" vandalism audits | Provenance on every assertion: who/when/which CR; ability to find all descendants of a bad edit |
| Insertion-order independence (commutative merges) | Merge semantics must not depend on arrival order |
| LLM agent swarms writing in parallel | Many concurrent writers to *isolated* branches/CRs; serialized merge into master is fine |
| Billions of nodes eventually, tiny start | Must not pick something that dies at 10⁷ entities; must not over-build now |

---

## 2. System-by-system findings (2026 state)

### 2.1 TerminusDB — git-for-data document/graph DB

- **What it is:** open-source document graph database (JSON documents + RDF triples underneath) with *native* git semantics: commits on every update, branch, merge, diff/patch, push/pull/clone, time-travel to any commit. Apache 2.0. ([terminusdb.org](https://terminusdb.org/), [github.com/terminusdb/terminusdb](https://github.com/terminusdb/terminusdb))
- **Health in 2026:** the original company (TerminusDB Ltd / TerminusCMS) stepped back; **DFRNT assumed stewardship in 2025** and is actively shipping — v12 released late 2025, v12.0.4/12.0.5 in Feb 2026, with 2026 work targeting "performance, stability and precision" (arbitrary-precision decimals, Allen interval algebra for temporal reasoning, timestamp range queries). ~3.4k stars, small but real community (Discord), 7 open issues / 2 PRs — activity is *moderate*, essentially a one-vendor-plus-community project. ([terminusdb.org](https://terminusdb.org/), [github.com/terminusdb/terminusdb](https://github.com/terminusdb/terminusdb))
- **Fit:** conceptually the closest single match to the project's laws (immutable layers, branch/merge/diff at the *database* level, schema-checked documents, datalog + GraphQL query). Allen-interval support in v12 is even suggestive for historical-interval queries.
- **Risks:** bus-factor/stewardship (one small company, DFRNT, keeping it alive); no public evidence of multi-billion-node deployments; merge tooling is diff/patch-based and conflicts are surfaced for manual resolution — i.e., merge is not commutative out of the box; scaling story is single-node-ish (delta-encoded layers) rather than distributed.

### 2.2 Dolt / DoltgreSQL — git-for-SQL

- **What it is:** MySQL-compatible SQL database with full Git semantics (branch, merge, diff, clone, log) on table rows, backed by a Merkle/prolly-tree storage engine. ([github.com/dolthub/dolt](https://github.com/dolthub/dolt))
- **Health in 2026: excellent.** **Dolt 2.0 shipped May/July 2026** — automatic GC + archive compression on by default, adaptive storage (30-50% footprint reduction), beta version-controlled vector indexes, and benchmark claims of being *faster than MySQL* on sysbench (from 10-20x slower a few years ago to +13% writes / +5% reads). This is the best-funded, most actively engineered "git for data" project. ([InfoQ, July 2026](https://www.infoq.com/news/2026/07/dolt-version-control/))
- **DoltgreSQL** (Postgres wire/SQL dialect, same storage engine) is **still beta** in 2026, but DoltHub states it is "ready for your production use case" with fast bug turnaround. ([github.com/dolthub/doltgresql](https://github.com/dolthub/doltgresql), [doltgres.com](https://www.doltgres.com/))
- **Scale reality check:** Dolt scales like a single-primary OLTP database; DoltHub's own guidance says memory is the limiting resource (provision RAM ≈ 10-20% of on-disk size; commit graph loaded into memory at startup). Millions of branches/versions are proven; *billions of rows on one primary* is where it gets expensive. ([DoltHub: Dolt at scale](https://www.dolthub.com/blog/2024-10-21-dolt-at-scale/), [Sizing your Dolt instance](https://www.dolthub.com/blog/2023-12-06-sizing-your-dolt-instance/), [Millions of versions](https://www.dolthub.com/blog/2025-05-16-millions-of-versions/))
- **Fit:** the *branch/merge/diff mechanics* are exactly the ChangeRequest lifecycle (branch = CR, PR-style review, merge to master, `dolt_diff`/`dolt_log` system tables give free audit). Cell-level three-way merge means non-overlapping edits merge cleanly regardless of order. But it's relational, not graph: the graph would be edge/node tables, traversals in SQL or exported to a graph runtime. Also MySQL dialect (Doltgres if you need Postgres).

### 2.3 XTDB — immutable bitemporal SQL (JUXT)

- **What it is:** immutable database where **every table is a SQL:2011 bitemporal table automatically** — valid-time + system-time columns maintained on every record, `UPDATE`/`DELETE` never destroy history, time-travel queries built in. Speaks SQL over the Postgres wire protocol + XTQL. ([docs.xtdb.com](https://docs.xtdb.com/), [xtdb.com/blog/launching-xtdb-v2](https://xtdb.com/blog/launching-xtdb-v2))
- **Health in 2026: good.** v2.0 GA'd 2025, **v2.1 (Dec 2025)** added multi-database support, **v2.2-beta (mid-2026)** adds leader election, Arrow ADBC/Flight SQL, GC of superseded compaction files. Storage is a distributed LSM over object storage (S3-class), which is a credible path to very large datasets. Backed by JUXT (consultancy), MPL-licensed core. ([github.com/xtdb/xtdb/releases](https://github.com/xtdb/xtdb/releases))
- **Fit:** immutability, audit ("as-of what we knew at time T"), and no-delete are *native and free*. **But there are no branches.** XTDB has one system timeline per database; there is no fork/merge primitive. ChangeRequests would still have to be app-level (staged documents or a scratch database), at which point XTDB is competing as "a nicer audit substrate," not as the branching engine.
- **Bitemporal caveat for this project:** see §4 (Q3). XTDB's valid-time is a *timestamp* axis for when a fact is true of the world **as an operational record**, not a vehicle for "Rome founded 753 BC ± 50y". Fuzzy deep-historical dates don't fit a timestamp-typed valid-time column and shouldn't be forced into it.

### 2.4 Datomic — immutable facts (datoms)

- **What it is:** the original immutable-facts database: every assertion is a datom `[entity attribute value tx added?]`, nothing is overwritten, full history queryable (`as-of`, `history`), transactions are first-class entities you can annotate (perfect provenance hook).
- **Licensing 2026: fully free.** Since April/June 2023, **Datomic Pro and Datomic Cloud are free (binaries Apache 2.0-licensed, no license keys)**, under Nubank's ownership; paid enterprise support optional. Still true in 2026. ([blog.datomic.com — "Datomic is Free"](https://blog.datomic.com/2023/04/datomic-is-free.html), [building.nubank.com](https://building.nubank.com/datomic-is-available-free-of-licensing-fees/))
- **Health in 2026: actively maintained** — Datomic Pro 1.0.7705 released **July 10, 2026**; multiple 2026 releases; Java 17 now required. ([docs.datomic.com/releases-pro.html](https://docs.datomic.com/releases-pro.html))
- **Fit:** single-timeline immutability + tx-entity provenance is a beautiful match for "no deletion, patient-zero audits." **No branches** — only `d/with` (speculative in-memory transaction application), which is enough to *preview* a ChangeRequest against current master but not to maintain long-lived shadow branches. Single-transactor writer = write-throughput ceiling; datom count practical ceiling historically cited ~10 billion datoms per DB. Clojure-centric tooling (peer/client libraries), closed source (free but not open source).

### 2.5 Fluree / FlureeDB — verifiable ledger knowledge graph (the notable 2026 entrant)

- **What it is:** RDF/JSON-LD knowledge graph database where **every transaction is an immutable, content-addressed commit on a tamper-evident chain**; time-travel to any commit/timestamp with a `t` parameter; SPARQL + JSON-LD query; optional JWS / W3C Verifiable Credential signing of every transaction. ([flur.ee/platform/core](https://flur.ee/platform/core), [Time traveling with Fluree](https://flur.ee/fluree-blog/time-traveling-with-fluree/))
- **2026 relaunch:** **FlureeDB GA'd June 2026**, explicitly positioned as a "verifiable knowledge graph database for agentic AI" — and it now advertises **branch + merge**: "Fork a dataset to test a schema change, a migration, **or an agent's proposed edits** in complete isolation, then merge when validated." That is literally the project's ChangeRequest use case as a marketed feature. Scale claims: first place on SPARQLoscope DBLP (561M triples) and **43ms geometric mean across 850 queries on Wikidata's 21.5B triples**. ([FlureeDB launch, June 2026](https://markets.financialcontent.com/stocks/article/gnwcq-2026-6-23-fluree-launches-verifiable-knowledge-graph-database-for-agentic-ai))
- **License caveat:** the new FlureeDB is **BSL 1.1, converting to Apache 2.0 three years after each release** — source-available, not OSI-open until conversion. Company is a PBC; production users include DoD, Morgan Stanley, AP, Dow Jones; last disclosed raise was a $10M Series A (2023). ([launch article](https://markets.financialcontent.com/stocks/article/gnwcq-2026-6-23-fluree-launches-verifiable-knowledge-graph-database-for-agentic-ai), [businesswire 2023](https://www.businesswire.com/news/home/20230420005076/en/Fluree-Closes-$10M-Series-A-Round-for-Web3-Data-Management-Modern-Data-Infrastructure))
- **Fit:** on paper the single best feature match: graph model + immutable commits + branch/merge + per-commit cryptographic provenance (vandalism audits with signatures!) + demonstrated Wikidata-scale reads. Risks: brand-new GA (June 2026 — months old), BSL license, single-vendor, merge semantics/conflict model not yet battle-tested publicly, and marketing-grade benchmarks need independent verification.

### 2.6 lakeFS / Project Nessie / Iceberg — data-lake branching

- **lakeFS:** git-like branch/commit/merge/revert over object-store data lakes, zero-copy branching at petabyte scale. **Nessie:** git-like commit graph as a *catalog* over Apache Iceberg tables (branches/tags across many tables; works with Spark/Trino/Dremio). Both healthy in 2026. ([lakefs.io](https://lakefs.io/data-version-control/), [Dremio comparison](https://www.dremio.com/blog/data-lakehouse-versioning-comparison-nessie-apache-iceberg-lakefs/))
- **Fit: wrong granularity.** These version *files/tables/snapshots*, not entities. Branch-per-ChangeRequest with row-level three-way merge of a graph is not what they do; merges are snapshot/table-level. Relevant later only for versioning derived analytical exports of the tree, not the system of record.

### 2.7 Platform-level branching (Neon, Turso, PlanetScale)

- Neon (acquired by Databricks for ~$1B, May 2025) does sub-second copy-on-write **database branches**, marketed for CI/preview environments; Turso similar. ([Neon vs Turso 2026 landscape](https://www.sabaoon.dev/blog/edge-database-landscape-2026), [techsy.io comparison](https://techsy.io/en/blog/neon-vs-planetscale-vs-turso))
- **Fit: wrong merge model.** These branches are for *disposable environments* — there is **no data merge back** (Neon "merges" by replaying the migration on main). Useless as the CR mechanism, though Neon-style branching is handy for dev/test environments of whatever store is chosen.

### 2.8 Event sourcing over a plain store

- The pattern is having a moment in the agent world: 2025-26 agent frameworks are explicitly event-sourced ("the log is the agent") — append-only event logs as the audit trail for LLM agent actions, e.g. [activegraph](https://github.com/yoheinakajima/activegraph) (event-sourced graph runtime for durable stateful agents) and the OpenHands SDK's immutable event log ([arxiv](https://arxiv.org/pdf/2511.03690)); research on compiling agent traces into event knowledge graphs for provenance ([arxiv 2606.04990](https://arxiv.org/pdf/2606.04990)).
- **Fit: strong.** An append-only `events`/`entity_versions` schema in Postgres gives: no deletion by construction, per-entity history, CRs as first-class rows, atomic revert = compensating events, patient-zero = walk the event log. The cost: you build diff/merge/branch-view yourself — but see §3 (that's what Wikidata/OSM did, deliberately).

### 2.9 CRDT-based stores

- **State of the art 2026:** the "CRDT war" consolidated to **Yjs** and **Automerge**. **Automerge 3.0 (Aug 2025)** re-architected to use its compressed columnar format in memory: ~10x (up to 100x) memory reduction (Moby-Dick doc: 700MB → 1.3MB), same file format, near-compatible API; production-viable. ([automerge.org/blog/automerge-3](https://automerge.org/blog/automerge-3/), [BigGo coverage](https://biggo.com/news/202508071934_Automerge_3.0_Memory_Improvements), [Local-first in 2026](https://verity.salient.community/research/local-first-software-in-2026.html))
- **ElectricSQL abandoned the CRDT approach**: mid-2024 clean rebuild into a read-path Postgres sync engine; writes go through your API. The most-funded CRDT-database attempt concluded that write arbitration belongs in the application. ([materializedview.io interview](https://materializedview.io/p/electricsql-pglite-crdts-and-elixir), [PowerSync comparison note](https://powersync.com/blog/electricsql-vs-powersync))
- **Ink & Switch "Patchwork"** (2024-26) is the frontier of *version-control UX on CRDTs*: lightweight branches as separate Automerge documents, visual diffs, review workflows — "universal version control." It's a research prototype, and notably it *re-introduces explicit branches and human review on top of CRDTs* rather than relying on automatic merge. ([inkandswitch.com/patchwork](https://www.inkandswitch.com/project/patchwork/), [universal version control essay](https://www.inkandswitch.com/universal-version-control/))
- **Fit:** see §4 (Q4). CRDT libraries solve *unattended* merge; the project's merge is *attended* (review-gated). What transfers is the discipline of commutative operations, not the library.

### 2.10 Adjacent 2026 graph-landscape notes

- **Kùzu (embedded graph DB) is dead** — repo archived Oct 2025, team acqui-hired (Apple); community weighing forks ([BigGo](https://biggo.com/news/202510130126_KuzuDB-embedded-graph-database-archived), [gdotv post-mortem](https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/)). A cautionary tale about betting the system of record on a small-team niche DB — directly relevant to how much weight to put on TerminusDB/Fluree stewardship risk.
- Successors in the embedded/graph space: FalkorDB, DuckPGQ, LadybugDB/bighorn forks — none offer version control, so none are candidates here.

---

## 3. What the real citable-fact systems do (Q2 evidence)

### Wikidata (~114-140M items, **2.5+ billion edits**, ~41k active users — [Wikidata:Statistics](https://www.wikidata.org/wiki/Wikidata:Statistics))
- **No storage-level branching. No branches at all.** Every edit goes *live on master immediately*; the unit of versioning is the **MediaWiki revision** — an app-level, per-entity, full-JSON-blob snapshot with user + timestamp + comment. Review is *post-hoc* (patrolling, watchlists, ML vandalism detection, reverts), not pre-merge. ([wikidata-wikibase-architecture](https://github.com/wmde/wikidata-wikibase-architecture/blob/main/Introduction.md))
- History at this scale is painful *as implemented*: 700M+ revisions live as compressed XML/JSON dumps (~250GB) rather than a queryable versioned graph; researchers rebuilt diff streams (per-revision RDF triple add/delete sets) as external datasets ([Wikidated 1.0](https://ceur-ws.org/Vol-2982/paper-11.pdf), [Querying the Edit History of Wikidata](https://link.springer.com/chapter/10.1007/978-3-030-32327-1_32)). The query service is a *downstream projection* that stresses under large-entity edits ([WDQS ScalingStrategy](https://wikitech.wikimedia.org/wiki/Wikidata_query_service/ScalingStrategy)).
- **Lessons:** (a) app-level revisions scale to billions of edits; (b) store *diffs or structured versions*, not opaque blobs, or history becomes an archaeology project; (c) keep the queryable projection separate from the system of record.

### OpenStreetMap
- **Changesets are the model the project already converged on:** a changeset groups related edits by one user/session; every element (node/way/relation) carries a monotonically increasing **version number** used for optimistic locking (edit rejected if you're not editing the latest version); old versions are kept forever in history tables; reverts are *new forward edits* computed from history, not deletions. Changesets are explicitly **not atomic** across the set (each upload request is atomic). ([OSM Changeset wiki](https://wiki.openstreetmap.org/wiki/Changeset), [API v0.6](https://wiki.openstreetmap.org/wiki/API_v0.6), [2008 changesets/reverts design doc](https://wiki.openstreetmap.org/wiki/Original_Changesets_and_Reverts_Proposal_2008))
- Vandalism auditing is a *tooling layer over changesets* (OSMCha, actively upgraded 2025 — [openstreetmap.us](https://openstreetmap.us/news/2025/05/osmcha's-new-upgrade/)) — the patient-zero workflow is "find bad changeset → compute revert → apply as new changeset."
- **Lessons:** (a) per-entity version counters + changeset grouping + optimistic locking is sufficient for a planet-scale collaborative graph; (b) atomic *section* rollback needs the changeset to be a first-class object you can invert; (c) OSM's non-atomic changesets are a known wart — the project can do better by making CR-merge transactional.

**Bottom line for Q2:** at Wikidata/OSM scale, nobody uses a branching database. Both use app-level change objects over boring stores, and their pain points (blob-history, non-atomic changesets, live-on-master editing with post-hoc review) are precisely the things the project's ChangeRequest design already fixes *at the application layer*. The precedent says: the review workflow is application domain logic; the store just needs append-only versions + provenance.

---

## 4. Answers to the key questions

### Q1. Who gives branches + immutable history natively at graph/entity granularity, and are they healthy?

| System | Native branch+merge | Entity/graph granularity | Immutable history | 2026 health | License |
|---|---|---|---|---|---|
| **TerminusDB** | Yes (branch/merge/diff/rebase-ish) | Yes (documents/triples) | Yes (layers) | Alive, DFRNT-stewarded, small community; v12.0.5 (2026) | Apache 2.0 |
| **Dolt** | Yes (full git semantics, cell-level merge) | Rows (relational, not graph) | Yes (prolly trees; GC of *unreferenced* garbage only) | **Excellent**; 2.0 (2026), faster than MySQL | Apache 2.0 |
| **DoltgreSQL** | Yes (same engine) | Rows | Yes | Beta, improving fast | Apache 2.0 |
| **FlureeDB** | **Yes (new: fork/merge for agent edits)** | Yes (RDF graph) | Yes (content-addressed, signable commits) | GA June 2026 — promising, unproven | **BSL 1.1** → Apache 2.0 after 3y |
| XTDB | No branches | Rows/docs | Yes (bitemporal, everything) | Good; v2.1/v2.2-beta (2025-26) | MPL |
| Datomic | No (only speculative `with`) | Datoms (EAV — graph-friendly) | Yes | Good; free; Pro 1.0.7705 (Jul 2026) | Free binaries, closed source |
| lakeFS / Nessie | Yes | Files / tables (too coarse) | Yes | Healthy | Apache 2.0 |
| Neon/Turso | Env-level branches, **no merge-back** | Whole DB | No (retention-window PITR) | Healthy | n/a (services) |

Only three real candidates give branches at the right granularity: **TerminusDB, Dolt(gres), FlureeDB** — respectively: right model / small project; wrong model (SQL) / strongest project; right model + right pitch / newest and least proven.

### Q2. Native branching vs app-level ChangeRequests?

Covered in §3. The at-scale precedent (Wikidata 2.5B edits, OSM) is unanimously **app-level change objects over a plain store**. Native-branching DBs are attractive because branch/diff/merge/audit come free and correct-by-construction; they cost you: project-survival risk (Kùzu lesson), scale ceilings (Dolt RAM ∝ disk; TerminusDB unproven at billions), dialect/ecosystem lock-in, and — critically — **the review-queue, CI validation, karma/trust, and patient-zero tooling are application features anyway**. The branching DB only replaces the *storage* of proposals, maybe 20% of the CR feature.

There is also a subtle mismatch: git-style branches are *long-lived lines of development*; CRs here are *short-lived proposal bundles* (more like Gerrit changes than git branches). Wikidata models a proposal as "a draft edit not yet applied"; OSM as "a changeset under upload." A CR = an unapplied, validated set of entity-version deltas — trivially representable as rows.

**Verdict:** default to **app-level ChangeRequests**; treat native branching as an implementation detail a future storage engine may provide, not as an architecture driver. If a native engine is adopted, map CR → branch 1:1 and keep the CR object as the source of review metadata regardless.

### Q3. Does bitemporality fit "facts with validity time + record time"?

**Partially — and the distinction matters.** Bitemporal systems give two axes:

- **System/transaction time** — "when did the database learn/assert this." The project **absolutely needs this axis**, and it is exactly what XTDB/Datomic/Fluree/TerminusDB all provide natively (append-only tx history). Any chosen store must have it (or an event log that *is* it).
- **Valid time** — "when was this true in the world." In XTDB/SQL:2011 this is a **timestamp-typed, precise interval** designed for operational facts ("address valid from 2024-03-01"). ([docs.xtdb.com key concepts](https://docs.xtdb.com/concepts/key-concepts.html), [Bitemporal modeling](https://en.wikipedia.org/wiki/Bitemporal_modeling))

The project's historical dates are **not** valid-time in this sense: they are *fuzzy scholarly claims* — decimal years, BC dates, uncertainty ranges, competing datings, calendar ambiguity — and they are themselves **citable facts subject to versioning and dispute**. Forcing "invented ~3500 BC ± 300y" into a `TIMESTAMP` valid-time column fails on representation (timestamp range/precision), on uncertainty (no ± semantics), and on epistemology (the DB's valid-time axis can't hold *two competing datings with different sources*; a fact table can). Note the SQL:2011 valid-time features have seen little real-world adoption precisely because they're rigid ([XTDB's own framing](https://docs.xtdb.com/intro/what-is-xtdb.html)).

**Verdict:** model historical time as **domain data** (e.g., `{year: -3500.0, uncertainty: 300, calendar: …, source: …}` on the fact), and use **transaction-time versioning** (event log / commit chain) as the only temporal axis the *store* owns. Bitemporal DBs are therefore not disqualified — XTDB would simply carry an unused-for-history valid-time axis — but bitemporality is *not a reason to pick them*, and it doesn't substitute for branches.

### Q4. Do CRDTs help?

**As a library/substrate: no. As a design discipline: yes.**

- CRDTs guarantee convergence for *unattended, automatic* merges. The project's pipeline has a **review gate**: a human/agent approves a CR, then it lands. Approval is an arbitration decision — inherently order-sensitive and non-commutative (two conflicting CRs: whichever merges first wins; the second must rebase/re-validate). No CRDT removes that; Ink & Switch's Patchwork — the most advanced CRDT-version-control work — *adds explicit branches, diffs, and human review on top of Automerge* rather than trusting auto-merge ([Patchwork](https://www.inkandswitch.com/project/patchwork/), [Universal Version Control](https://www.inkandswitch.com/universal-version-control/)). ElectricSQL's pivot away from CRDTs to "writes go through your API" is the same conclusion from industry ([materializedview.io](https://materializedview.io/p/electricsql-pglite-crdts-and-elixir)).
- Automerge-per-entity is also operationally wrong here: full per-document CRDT metadata for billions of small entities, and (even at 3.0's 10-100x improvement — [automerge.org](https://automerge.org/blog/automerge-3/)) the history-bearing document model targets thousands of documents, not 10⁹ graph nodes.
- **What to steal from CRDTs — the insertion-order-independence law is really a "design your operations to commute" law:**
  - Facts as **grow-only sets** of immutable assertions (add-only; retraction = new status-assertion) → G-Set/2P-Set semantics; set-union merges commute.
  - Entity IDs content-derived or UUID (no auto-increment) → parallel creation commutes.
  - Field updates carry (CR-id, timestamp, provenance) → deterministic LWW *with full history retained*, so "last-writer" is an index choice, not data loss.
  - Merge-redirects as monotone union-find style records → commutative.
  - Reserve *non-commutative* decisions (conflicting values, schema changes) for the review gate, and make the merge operation detect exactly those.

**Verdict:** don't adopt a CRDT store; write the CR-apply function as commutative set-union over immutable assertions, which satisfies the invariant for all non-conflicting CRs and routes true conflicts to review — which is where they belong.

---

## 5. Candidate shortlist with judgments

1. **App-level CR schema on Postgres (append-only)** — *primary recommendation.* Zero project risk, exact-fit semantics, Wikidata/OSM-proven pattern, trivially portable later. You build: diff (cheap over structured versions), CR-apply (set-union), revert (inverse changeset), audit (walk the log). All of these are small compared to the review/trust system you must build regardless.
2. **FlureeDB** — *strongest native candidate; run a spike.* Graph model + immutable signed commits + fork/merge for "an agent's proposed edits" + claimed 21.5B-triple Wikidata benchmark is a stunning on-paper match ([launch](https://markets.financialcontent.com/stocks/article/gnwcq-2026-6-23-fluree-launches-verifiable-knowledge-graph-database-for-agentic-ai)). Held back from "adopt now" by: 2-month-old GA, BSL 1.1, single vendor, unverified merge-conflict semantics under swarm write load.
3. **Dolt / DoltgreSQL** — *most trustworthy native engine, wrong shape.* If the ground-fact schema flattens well into a handful of tables (it does: nodes, assertions, edges, sources), Dolt gives industrial-grade branch/merge/diff with real momentum ([Dolt 2.0](https://www.infoq.com/news/2026/07/dolt-version-control/)). Watch the RAM-∝-disk scaling profile before believing "billions."
4. **TerminusDB** — *conceptual soulmate, stewardship risk.* Fine for a prototype of what branch-native graph feels like; would not bet the system of record on it today ([DFRNT-era status](https://terminusdb.org/)).
5. **XTDB / Datomic** — *adopt their ideas (immutable facts, tx provenance, as-of queries), not necessarily the products*, since neither has branches and the CR layer would be app-level anyway. Datomic is free and battle-hardened ([free since 2023](https://blog.datomic.com/2023/04/datomic-is-free.html), [Pro releases through Jul 2026](https://docs.datomic.com/releases-pro.html)); XTDB v2's object-storage LSM is the more modern scale story ([releases](https://github.com/xtdb/xtdb/releases)).
6. **lakeFS/Nessie, Neon/Turso, CRDT stores** — not candidates for the system of record (granularity / no merge-back / wrong merge model respectively).

---

## 6. Recommended architecture direction

**Build app-level ChangeRequests over an append-only Postgres core; design the schema so a native-branching graph engine (FlureeDB, or Dolt as the conservative pick) can be adopted later as either (a) the materialized master projection or (b) the full system of record, without changing the CR model.**

Sketch:

- `entities(id, kind, lifecycle_status, redirect_to, current_version_id)` — current pointers only (a projection, rebuildable).
- `entity_versions(id, entity_id, version_no, body_jsonb, created_by_cr)` — immutable; OSM-style optimistic version counter.
- `assertions(id, entity_id, field/edge, value, source_ref, historical_date jsonb, status)` — immutable ground facts; historical fuzzy dates live *here* as data (Q3).
- `change_requests(id, status: draft|validated|approved|merged|rejected, base_versions jsonb, deltas jsonb, author_agent, reviews …)` — the shadow branch. Deltas are add-only assertion sets + status changes; apply = commutative union; conflict = base-version mismatch on a contested field → back to review (Q4).
- `merge_log(cr_id, tx_time, inverse_delta)` — atomic section rollback = apply inverse delta as a new CR; patient-zero = transitive closure over `created_by_cr`.

This is Wikidata's revision model + OSM's changeset model + Datomic's tx-provenance idea + CRDT-style commutative deltas — with none of their historical mistakes (blob revisions, non-atomic changesets, live-on-master editing).

**Decision triggers to revisit native branching:**
- FlureeDB: still shipping + independent scale/merge reports by mid-2027, and BSL acceptable → prototype master-projection on it (SPARQL + signed commits are big wins for a citable-facts project).
- Dolt: if graph traversal needs stay modest and dataset < ~1TB working set, Doltgres GA would make it a credible full system of record.
- TerminusDB: monitor DFRNT stewardship; reassess if community/investment grows.

---

## 7. Source index

- TerminusDB: https://terminusdb.org/ · https://github.com/terminusdb/terminusdb · https://en.wikipedia.org/wiki/TerminusDB
- Dolt 2.0: https://www.infoq.com/news/2026/07/dolt-version-control/ · https://github.com/dolthub/dolt · https://www.dolthub.com/blog/2024-10-21-dolt-at-scale/ · https://www.dolthub.com/blog/2025-05-16-millions-of-versions/ · https://www.dolthub.com/blog/2023-12-06-sizing-your-dolt-instance/ · https://github.com/dolthub/doltgresql
- XTDB: https://docs.xtdb.com/ · https://github.com/xtdb/xtdb/releases · https://xtdb.com/blog/launching-xtdb-v2 · https://docs.xtdb.com/concepts/key-concepts.html
- Datomic: https://blog.datomic.com/2023/04/datomic-is-free.html · https://building.nubank.com/datomic-is-available-free-of-licensing-fees/ · https://docs.datomic.com/releases-pro.html
- Fluree: https://markets.financialcontent.com/stocks/article/gnwcq-2026-6-23-fluree-launches-verifiable-knowledge-graph-database-for-agentic-ai · https://flur.ee/platform/core · https://flur.ee/fluree-blog/time-traveling-with-fluree/
- lakeFS/Nessie: https://lakefs.io/data-version-control/ · https://www.dremio.com/blog/data-lakehouse-versioning-comparison-nessie-apache-iceberg-lakefs/
- Neon/Turso: https://www.sabaoon.dev/blog/edge-database-landscape-2026 · https://techsy.io/en/blog/neon-vs-planetscale-vs-turso
- Wikidata: https://www.wikidata.org/wiki/Wikidata:Statistics · https://github.com/wmde/wikidata-wikibase-architecture/blob/main/Introduction.md · https://ceur-ws.org/Vol-2982/paper-11.pdf · https://wikitech.wikimedia.org/wiki/Wikidata_query_service/ScalingStrategy · https://link.springer.com/chapter/10.1007/978-3-030-32327-1_32
- OSM: https://wiki.openstreetmap.org/wiki/Changeset · https://wiki.openstreetmap.org/wiki/API_v0.6 · https://wiki.openstreetmap.org/wiki/Original_Changesets_and_Reverts_Proposal_2008 · https://openstreetmap.us/news/2025/05/osmcha's-new-upgrade/
- CRDTs: https://automerge.org/blog/automerge-3/ · https://biggo.com/news/202508071934_Automerge_3.0_Memory_Improvements · https://www.inkandswitch.com/project/patchwork/ · https://www.inkandswitch.com/universal-version-control/ · https://materializedview.io/p/electricsql-pglite-crdts-and-elixir · https://verity.salient.community/research/local-first-software-in-2026.html
- Event-sourced agent runtimes: https://github.com/yoheinakajima/activegraph · https://arxiv.org/pdf/2511.03690 · https://arxiv.org/pdf/2606.04990
- Landscape: https://biggo.com/news/202510130126_KuzuDB-embedded-graph-database-archived · https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/
