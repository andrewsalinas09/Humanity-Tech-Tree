# ADR-0007: People connect via their works; the human layer is a parallel graph

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** abstraction-chat digest; README

## Context
Should Calculus depend on Isaac Newton? If people are mechanical dependencies, the graph claims no one else could have discovered it — and independent discovery (Newton/Leibniz) breaks.

## Decision
People connect through WORK_PUBLICATION nodes: Person → AUTHORED → Work → codifies → Concept. Multiple works can point at one concept (independent discovery for free). Possibility/validation traversal *ignores* authorship edges: "A tech is possible when its Physics are met, not when its Author is born." Exception: events where the person genuinely is the dependency (WWI → Franz Ferdinand) may link directly. The human layer is a parallel "Did Happen" graph over the deterministic "Must Happen" engineering tree; default rendering hides it ("Ghost Edges"), History Mode fades it in.

## Why
"WiFi needs Hedy Lamarr, but only because she did. Any other person could have done that." Separating contingent history from necessary dependency keeps first-principles queries clean while preserving full historical credit.

## Consequences
`KNOWLEDGE_REQUIREMENT` edges give the human layer its own validation ("Time Gate": a person cannot predate their prerequisite knowledge). Whether human edges ever participate in unlock logic is open (Q-14).
