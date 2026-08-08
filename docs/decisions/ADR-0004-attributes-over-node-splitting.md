# ADR-0004: Attributes over node-splitting (the DigiKey problem)

- **Status:** Accepted
- **Date:** ~2026-01 (see git commit "solveing the issue of specifying specicif needs like purity levels")
- **Source:** long-chat digest

## Context
Modeling every variant as a node (1kΩ resistor, 10kΩ resistor, 99% lithium, 99.999% lithium) explodes into millions of SKU nodes — the "DigiKey problem."

## Decision
One generic node + a dynamic attribute system. `AttributeRegistry` interns attribute names to uint32 IDs; process nodes carry `AttributeModifier`s (SET/ADD/MULTIPLY); consumer edges carry `AttributeConstraint`s (GT/LT/EQ/CONTAINS). The solver stacks optimizer processes (the "Modifier Stack") into a virtual material instance until constraints pass. Specific requirements like purity are satisfied by *optimization paths*, never by variant nodes.

**The Manufacturing Test** decides node vs. attribute: new node only when the bill of materials / physics / supply chain changes (Li-ion vs lead-acid = nodes; purity levels and resistance values = attributes). When in doubt, **Lazy Split**: start as an attribute — splitting later is easy, merging nodes is hard.

## Why
Virtual instances computed at solve time cost nothing to store, and new refinement tech added later is picked up automatically with zero downstream edits. The attribute vocabulary is deliberately not pre-enumerated — an LLM co-pilot canonicalizes free text ("very flat" → `Surface_Roughness_RMS`).

## Consequences
The solver owns constraint evaluation and modifier stacking (C++, ADR-0010). Attribute name hygiene needs LLM-assisted canonicalization to avoid synonym drift.
