# ADR-0009: The Significance Filter gates node creation; minor versions are data, not nodes

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** abstraction-chat digest

## Context
The "Data Explosion" problem: 16 iPhone nodes, 500 near-identical sedans, every CPU stepping — at scale this is 50,000 nodes of noise that drowns the tree.

## Decision
A node is created only if it passes at least one of six rules:
1. **Progenitor** — first of its class (Benz Patent-Motorwagen)
2. **Bridge** — has a cross-domain child (Jacquard Loom → Babbage)
3. **Keystone** — deleting it breaks a dependency chain (V-2 → Apollo)
4. **Scale** — standardized the tech for humanity (Model T)
5. **Divergence** — a distinct losing branch (Betamax; dead ends are as educational as winners)
6. **Icon** — cultural anchor (Titanic, Chernobyl)

Everything else lives as data: series-root nodes hold a `ProductIteration` list (name, year, key feature, optional tech links), and paradigms carry a `minor_examples` list. Worked example: GameCube fails all six (iteration); Wii passes Divergence (new MEMS-accelerometer dependency) and gets a node.

## Why
"Only create a node when the object changes the dependencies or capabilities of the tree." Keeps the graph a map of *causal structure*, not a product catalog, while iterations remain browsable inside their series node.

## Consequences
This is editorial policy for contributors and ingestion scripts alike. Sibling artifacts sharing a paradigm earn nodes via their unique inputs (Civic ← CVCC; Corolla ← TQM).
