# Vision

A tech tree for all of humanity — technology **and** culture — as a single knowledge graph where edges are dependencies from parent to child.

## North-star goals

1. **Show how technology bootstrapped itself.** Iron makes tools, tools make steel, steel makes better tools. These loops must terminate via optimization edges — and the number of loop iterations needed varies by target (an airplane turbine blade needs many more bootstrap cycles than a horseshoe).
2. **First-principles derivation.** Given any node, trace the full dependency chain down to natural laws and raw materials. "What would it actually take to build X from scratch?"
3. **Truth with texture — show the mess.** History is messy, and the graph must show the mess or it isn't faithful; nothing is ever simplified into a lie for convenience. Edges carry epistemic status (mainstream fact → mythology), validity status (current truth → disproven), fuzzy dates with uncertainty ranges, regional timelines where knowledge is gained, *lost*, and regained (Roman concrete), corporate lineages with spin-offs and brand transplants, and dead ends kept on purpose. Click the newest Keysight scope and you can walk back through Agilent to HP to two founders in a garage in 1939 — every hop dated, every hop honest.
4. **Crowdsourced, but vandal-proof.** Editable by anyone at the leaves, protected in proportion to how much depends on a node, with shadow branches, review queues, reputation, and automated sanity checks.
   *The dual audience is one system:* research-grade and citable (verification floors, confidence traces, versioned scoring) AND genuinely fun (red badges and contested bands ARE the game board; bounties everywhere). Same fact base, two lenses.
5. **Realistic paths without lying.** Technically-true edges stay in the graph (you *could* build a computer from vacuum tubes); constraints on edges prune paths to what's actually viable for a use case. Broken paths become visible bounties ("iPhone has no valid path through battery") that gamify fixing the graph.
6. **The invisible dependency structure of knowledge, made queryable.** The graph holds what today lives only in experts' heads: the Riemann Hypothesis's *children* — every theorem proven assuming it, and how much falls if it's false (impact analysis on a conjecture); how Galois theory quietly parents results in quantum mechanics and other distant fields; the child tree a room-temperature superconductor would unlock the day it exists. Hypothetical nodes (0 parents, validity: hypothetical) let people build the *future's* child tree in advance — one validity flip cascades the unlock through every descendant. The same counterfactual query that asks "could Rome have steam engines?" asks "what would X depend on in theory?" — the graph as invention prospector: get the gap list, invent the gap, add the facts, watch it unlock.

## Why now

This project was impossible before LLMs. The graph needs millions of judgment calls — "does this edge belong on the abstract node or the instance?", "is this semantic connection plausible?" — that only scale with an AI in the loop for triage, with humans reviewing. LLM agents are also how the graph gets built and maintained, which is why this repo's documentation system is designed for agent handoff (see `CLAUDE.md`).

## What this is not

- Not a taxonomy or encyclopedia — Wikipedia has articles; this has *dependencies*.
- Not a general history database — **the tech tree is first-class**; events, people, and organizations enter only where they shape technology (WWII is here because of radar and rocketry, not for its own sake).
- Not a curated expert-only database — the moderation design exists precisely so it can be open.
- Not required to be perfect — "let true things be true and it's ok if it's not perfect." Constraints and community flags converge it toward accuracy over time.
