# ADR-0014: Build order — tracer-bullet solver first, public UI last

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
The temptation is to start with the pretty graph website. But every hard risk in this project lives in the solver semantics (constraints, optimization paths, state-as-query), and a UI built first would calcify a broken schema.

## Decision
1. **God-Mode tracer bullet:** hardcoded nodes in C++ → solver → Graphviz `.dot` dump (green = active path, red = rejected). No database, no web.
2. Prove a **"Golden Spike" vertical slice** end-to-end (e.g. Boolean Logic → Vacuum Tubes → Transistor → Intel 4004), demonstrating constraint pruning (the vacuum-tube iPhone dies on a Switching Speed attribute) and a bootstrap loop resolving generationally.
3. **Read-only viewer** (Cytoscape.js / React Flow candidates — not committed) over Neo4j.
4. **Editor + moderation stack**, then public write access.

## Why
The tracer bullet is the cheapest possible test of the riskiest claims. Impact Analysis ("kill Photolithography, watch the tree die") falls out of the same debugger. "Prove the iPhone/RISC-V pruning visually before any web frontend."

## Consequences
Roadmap Phase 1 is a C++ console program with Graphviz output. Frontend stack choice (Q-12) can stay open until Phase 3 without blocking anything.
