# SOTA research: embeddings & the find-or-create gate (2026-08-09)

Three parallel research tracks (model landscape & retrieval architecture; graph-aware embeddings & entity resolution; production find-or-create systems), commissioned on the user's call: "the embedding is probably one of the most important things that makes this whole thing work." Full agent reports in session; this is the synthesis. All claims carry sources in the originals.

## Validation: what we already built is the right shape
- **Serialized-neighborhood text embeddings are the pragmatic SOTA**, not a stopgap. The text-attributed-graph literature (TAPE, STAGE, LLM+TAG surveys) converged on "the winning move is better text, not better graph math." Learned alternatives (node2vec, TransE-family) are transductive — a new node can't embed without retraining — dead on arrival against ADR-0054. Inductivity scorecard in report 2. Keep the substrate.
- **The receipt design matches production best practice** (Stripe idempotency + Discogs attestation, independently converged).
- **Hash-gated re-embedding** = Notion's Page State pattern (−70% reprocessing). Already ours.
- **Serialization must stay strictly 1-hop** — that's what bounds the re-embed cascade to {A, B} per new edge (GNN systems fight k-hop cascade blowup with whole research systems; 1-hop text makes the problem not exist).
- **The reconcile-before-create gate is the load-bearing mechanism** at Wikidata too (they do NO automated merging). Sobering number: Wikidata runs ~3.6% lifetime duplicate rate, and **bot-created duplicates outnumber human 3:1** — agent swarms are the dominant duplicate source. Our unskippable gate for agents is THE critical control, not a nicety.

## What's provably behind (the upgrade list)
1. **Model**: bge-small-en-v1.5 (2023) is retired-class. Local default candidate: **Qwen3-Embedding-0.6B** (Apache 2.0, 1024d MRL, instruction-aware). Strategic spike: **voyage-4-nano** — open weights sharing the embedding space with Voyage's paid API family, meaning later API-quality upgrades need NO corpus re-embed (unique on the market).
2. **Hybrid retrieval is mandatory for our corpus shape** (short codes, alias-heavy names — "802.11ax", "D2"): dense + real BM25 (VectorChord-bm25 / ParadeDB / pg_textsearch — native ts_rank lacks IDF) + pg_trgm on names/aliases (typos; Algolia calibration: 1 typo ≥4 chars, 2 ≥8) → **RRF fusion** → top-50 → **cross-encoder rerank** (bge-reranker-v2-m3, self-hosted) whose pairwise score IS the gate's decision score. Hybrid buys 15–30% recall; ColBERT rejected (wrong shape for 2-sentence cards).
3. **Three-band gate decision** (OpenRefine/Discogs, calibrated never hard-coded): HIGH = block-and-offer-existing; MIDDLE = create only with **per-candidate explicit rejection + rationale recorded on the receipt** (structured field for agents, checkbox+text for humans) + "create as variant of X" offer; LOW = create freely, receipt records top-k. Wikidata trick: type mismatch HALVES score, never hides. Prime-directive mapping: missed dup = incompleteness (tolerable); false merge = wrongness (auto-band stays conservative).
4. **Prefix policy**: dedup is symmetric (doc-vs-doc, no instruction); the search box is asymmetric (task instruction on the query side only). We currently treat both the same — accidentally right for the gate, suboptimal for search.
5. **Identity/context vector split** (consider): stable identity vector (name+aliases+description — the dedup signal, ~never invalidated) + context vector (neighborhood — staleness-tolerant, powers discovery). Decouples the gate from the cascade entirely.
6. **Golden set + eval harness FIRST**: ~500–1000 pairs — dup pairs (aliases, LLM paraphrases, programmatic typos, cross-register "tool steel for dies"→D2) + hard negatives (sibling concepts — the sibling-linter output is a generator). Metrics: duplicate recall@k (10/25/50), false-merge rate at threshold, MRR@10 for search. EVERY choice above gets ratified by this table, not leaderboards; it's also the mandatory validation in every model migration.

## The merge flywheel (the payoff loop)
On every confirmed merge, **replay the loser's creation receipt**: survivor absent from candidates → RECALL failure (fix: add the query as an alias first — cheapest; then fine-tune data); survivor present but rejected → PRESENTATION/attestation failure. Dashboard both + duplicate-rate by contributor class (expect agents to dominate). Merged pairs = gold positives; receipt-rejected non-dups = gold hard negatives (NV-Retriever-style fine-tunes, +5–10% retrieval in production loops). Merges are cheap, audited, reversible-by-record — prevention asymptotes below 100%, so merge tooling is non-optional.

## Campaign & sentinel machinery (Q-27/Q-28 support)
- Candidate discovery: relation-verbalized query embeddings ("things that require electric power to operate", facet-expanded) + **type-propagation** (8 of 10 siblings consume X ⇒ the rest are candidates — no ML, highest precision). ULTRA (pretrained zero-shot link predictor, inference-only) in reserve as a batch suggestion miner.
- Absurdity sentinel (ADR-0013): per-relation + per-category-pair cosine-distribution outlier scoring (training-free, derived data) → LLM/NLI judge only on the flagged tail → flags, never deletions.

## Ops roadmap
- **Now → ~5M**: pgvector HNSW (m=16, efc=64), halfvec day-one (~zero loss, half storage), 256–512d via MRL as needed; queue-on-write embedding pipeline (outbox/pgmq; O(1) per fact); staleness ≤1min on the gate path + a synchronous normalized-label lexical check at create time as the last line (staleness on THIS workload directly causes duplicates); REINDEX CONCURRENTLY scheduled (merge-heavy graphs bloat HNSW; dead tuples silently kill recall).
- **~5–30M**: VectorChord (100x faster builds) or pgvectorscale DiskANN; dedicated read replica; search stays behind the service verb so the backend is swappable.
- **30M+ / 10^9**: vector plane splits from Postgres (system of record stays); object-storage-first engines (Turbopuffer/LanceDB/Milvus-on-S3) are the only sane economics at 10^9 (Cursor −95% cost, Notion 10B vectors). Dual-write via the outbox, shadow-read on the merge eval set, atomic cutover.
- **Model migrations are CHEAP for us** (short docs): full re-embed ≈ $1–7K even at 10^9 via batch APIs — a budgeted event. Blue-green dual-column; thresholds DO NOT transfer between models (recalibrate bands on the golden set); never mix models in one index; receipts record model version.
- Agent-scale: idempotency keys on create; exact + semantic query caching (60–86% cost cuts in production); campaigns on the batch path.

## Recommended build order
1. Golden set + eval harness (gates everything).
2. Trigram arm + RRF fusion (biggest recall win per effort; pure Postgres).
3. Model bake-off on the harness: Qwen3-0.6B vs voyage-4-nano vs current (then swap via dual-column).
4. Reranker + three-band decision + middle-band attestation on receipts.
5. Identity/context vector split when edge-churn warrants.
6. Queue-on-write pipeline at production bake; merge flywheel dashboards when merges begin.
