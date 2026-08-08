# ADR-0002: Node state is the result of a query, not a stored property

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
The "Gunpowder Paradox": in 900 AD gunpowder is REALIZED in China and LOCKED/THEORETICAL in Europe. A single `current_state` field on the node can only hold one answer.

## Decision
LOCKED / THEORETICAL / REALIZED is computed from (Time + Location + Node) against regional timelines and dependency satisfaction. It is never authored by hand.

## Why
Stored state is wrong the moment the user moves a time slider or region filter. State is a *view*, like a spreadsheet cell formula.

## Consequences
`NodeState current_state` in `Node.cpp` is at most a cache for abstract-node realization (derived from instance activity), and should be treated as vestigial. Any feature that "sets" state is a design smell.
