# ADR-0012: Contributors use safe verbs and templates, never raw edge-drawing

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest

## Context
Volunteers "don't know what they don't know." Free-form node/edge editing produces topology mistakes (wrong direction, wrong granularity, duplicates) faster than reviewers can fix them.

## Decision
The editing UI exposes four wizard verbs — **Refine This** (add child), **Abstract This** (group under new parent), **Intercept** (insert a middleman on an edge), **Componentize** (attach a dependency) — plus a Pattern/Template library ("Device", "Standard", "Material", "Software") where contributors fill blanks. Node creation is search-first against names *and* `aliases` to defeat synonym duplicates (Petrol/Gasoline). All verbs compile to non-destructive operations (ADR-0011).

## Why
Verbs make the safe path the easy path: every wizard action preserves invariants (direction, archival of replaced edges) by construction. Templates encode the granularity conventions that would otherwise take a style guide nobody reads.

## Consequences
The four verbs + templates define the edit API surface the backend must support; raw editing remains an admin-only "god mode" tool.
