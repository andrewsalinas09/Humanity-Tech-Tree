# ADR-0011: Nothing is ever deleted; version-control fields ship in the schema from day one

- **Status:** Accepted
- **Date:** ~2026-01
- **Source:** long-chat digest; abstraction-chat digest

## Context
A crowdsourced graph will accumulate mistakes, duplicates, vandalism, and obsolete entries. Hard deletion destroys history, breaks referrers, and makes vandalism unrecoverable.

## Decision
Delete is replaced by: **Merge** (`MIGRATED_TO` redirect to the canonical node), **Deprecate** (lifecycle status ACTIVE/DEPRECATED/MERGED/VANDALISM; soft path-penalty via EXPERIMENTAL/MAINSTREAM/LEGACY/OBSOLETE + `deprecated_year`), and **Archive** (edge splits keep the old edge, archived). Every entity carries version-control fields (`version_uuid`, `previous_version_id`, author, timestamp, change_summary) from the first prototype, even while unused. Obsolescence applies to *methods* (TTL logic), not *components* (BJTs are still current in RF).

## Why
Bolting wiki-style history onto a graph DB later is a painful migration. Built-in versioning enables atomic rollbacks of graph sections and "patient zero" audit trails for vandalism. Non-destructive edits are what make "anyone can refine the graph" safe.

## Consequences
Storage grows monotonically; queries must filter by lifecycle status. Rollback tooling becomes possible and expected.
