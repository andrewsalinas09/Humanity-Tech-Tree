# ADR-0010: Neo4j stores the graph; a C++ solver owns the logic

- **Status:** Superseded in part by ADR-0031 (Neo4j replaced by Postgres-first; the fat-query → in-memory-solver split is reaffirmed and survives)
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
First-principles queries are deep recursive traversals ("X depends on Y depends on Z…"), which collapse relational SQL performance — Gemini's framing: Wikipedia-era MySQL is why this project wasn't buildable in 2001. Meanwhile the solve logic (constraint intersection, modifier stacking, overrides) is too intricate for query languages.

## Decision
Neo4j is the storage/traversal layer: a "fat query" pulls the relevant subgraph. All decision logic — override resolution, constraint checking, modifier stacks, LCA diagnostics, cycle detection, temporal validation — lives in C++ over the in-memory subgraph. Attribute maps serialize as JSON properties on Neo4j entities. Explicit anti-pattern: one giant clever Cypher query.

## Why
Giant Cypher becomes write-only code. C++ logic is unit-testable (`assert(solve(iPhone20)==RISCV)`), debugger-steppable, and nanosecond-fast in memory. Neo4j's graph algorithms additionally serve Sybil/botnet detection and version-audit trails. Scale risk is traversal cost, not storage — addressed by LOD separation (the simulation layer never walks blueprint-level detail).

## Consequences
Two runtimes to build and keep in sync (schema serialization boundary). Prototype phase can defer Neo4j entirely — the tracer bullet runs hardcoded in-memory data (ADR-0014).
