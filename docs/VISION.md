# Vision

A tech tree for all of humanity — technology **and** culture — as a single knowledge graph where edges are dependencies from parent to child.

## North-star goals

1. **Show how technology bootstrapped itself.** Iron makes tools, tools make steel, steel makes better tools. These loops must terminate via optimization edges — and the number of loop iterations needed varies by target (an airplane turbine blade needs many more bootstrap cycles than a horseshoe).
2. **First-principles derivation.** Given any node, trace the full dependency chain down to natural laws and raw materials. "What would it actually take to build X from scratch?"
3. **Truth with texture.** The graph doesn't pretend history is clean. Edges carry epistemic status (mainstream fact → mythology), validity status (current truth → disproven), fuzzy dates with uncertainty ranges, and regional timelines where knowledge can be gained, *lost*, and regained (Roman concrete).
4. **Crowdsourced, but vandal-proof.** Editable by anyone at the leaves, protected in proportion to how much depends on a node, with shadow branches, review queues, reputation, and automated sanity checks.
5. **Realistic paths without lying.** Technically-true edges stay in the graph (you *could* build a computer from vacuum tubes); constraints on edges prune paths to what's actually viable for a use case. Broken paths become visible bounties ("iPhone has no valid path through battery") that gamify fixing the graph.

## Why now

This project was impossible before LLMs. The graph needs millions of judgment calls — "does this edge belong on the abstract node or the instance?", "is this semantic connection plausible?" — that only scale with an AI in the loop for triage, with humans reviewing. LLM agents are also how the graph gets built and maintained, which is why this repo's documentation system is designed for agent handoff (see `CLAUDE.md`).

## What this is not

- Not a taxonomy or encyclopedia — Wikipedia has articles; this has *dependencies*.
- Not a curated expert-only database — the moderation design exists precisely so it can be open.
- Not required to be perfect — "let true things be true and it's ok if it's not perfect." Constraints and community flags converge it toward accuracy over time.
