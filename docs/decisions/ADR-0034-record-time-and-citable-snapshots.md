# ADR-0034: Record time is first-class — as-of views and citable snapshots

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user directive, restart session 3 ("see the citations for a set of nodes AT THE TIME and also CURRENT")

## Context
The graph will be cited in papers. Reproducibility demands that anyone can later retrieve exactly what the graph asserted — nodes, edges, citations, verification levels, confidence — at the moment it was cited, alongside the current state and the diff between them.

## Decision
1. **Three time axes, never conflated:**
   - **Historical time** — when things existed in the world (domain data: DatePoints, regional timelines).
   - **Possibility time** — earliest-possible entailments (ADR-0025).
   - **Record time** — when the *graph* learned/asserted something. Every stored fact/event carries it (the append-only log provides this structurally; ADR-0011/0026/0031).
2. **As-of queries are universal:** every query accepts an optional record-time `T`; the entire entailment stack (node state, effective dependencies, ladder levels, confidence) evaluates over facts with record time ≤ T. Reproducing a past confidence score pins the formula version, verifier model versions, and embedding versions that were current at T — this is why all of those are versioned (ADR-0032/0033).
3. **Citable snapshot references:** stable, resolvable identifiers ("as-of 2031-03-15", or a content-hash permalink, DOI-style) suitable for academic citation; resolving one yields the as-of view.
4. **Diffable citation exports:** for any node-set, export the citation/verification bundle as-of T AND current, with a structured diff ("source X retracted 2033; claim Y decomposed into Y1/Y2; confidence 97→81"). Papers citing the graph age *visibly*, never silently.
5. **Record time is append-only truth about the graph itself** and is never edited — even corrections are new records ("we asserted X at T1; we retracted it at T2" both remain forever), which is what makes patient-zero audits (ADR-0011) and honest as-of views possible.

## Why
This is what "research-grade" (ADR-0033 motivation) concretely requires: a citation to a living database is worthless unless the cited state is permanently retrievable. The design cost is near zero because the facts-only, append-only constitution already stores everything needed — this ADR promotes it from storage property to product surface. It also completes the never-wrong story across time: the graph may assert something at T1 that is later refuted; the as-of view shows what was asserted *then*, labeled as then — a true statement about the graph's history, not a falsehood.

## Consequences
- Postgres schema (ADR-0031): assertions carry record-time columns (created/superseded) — already in the sketch; as-of predicates become standard query fragments.
- MCP: `export_citations(node_set, as_of?)` tool; every read accepts `as_of`.
- Snapshot permalink scheme defined with the v1 schema doc (date-based + content-hash).
- Performance note for scale: as-of on hot paths may need periodic snapshot materialization — caches, never authorities (ADR-0026).
- TB-046 added.
