# ADR-0005: The Consumer defines the Need

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
Where do requirements like "99.9% pure lithium" live — on the lithium node, the battery node, or somewhere else? If the ingredient carries the spec, every consumer inherits it wrongly (grease doesn't need battery-grade lithium).

## Decision
Requirements and constraints are declared on the *consuming edge*, never on the ingredient node. Each node translates incoming high-level demands into its own lower-level demands (Chain of Responsibility: iPhone constrains CPU performance → CPU constrains transistor process → transistor constrains silicon purity). Rule: "You only constrain the things you physically touch." Cross-cutting policies can be attached at a root and carried down the recursion ("Bag of Rules", strictest-wins).

## Why
One shared ingredient node can serve consumers with wildly different specs, and updating one product never ripples into others. It also mirrors how real engineering specs flow.

## Consequences
Authoring an edge requires knowing that component's real requirements — the "Expertise Gap" (Q-08) — mitigated by LLM-suggested constraints and requirement templates.
