# ADR-0045: Citation sources are plain identifiers; work-nodes only by significance

- **Status:** Accepted (amends ADR-0038's citation shape; ADR-0038 otherwise stands)
- **Date:** 2026-08-09
- **Source:** user ruling ("that shouldn't be a node, that's a citation with a link / doc-id under sources — and it should be for a specific claim")

## Context
ADR-0038 made citations target assertions and reference a source node; the always-connected rule laid a `documents` thread from every cited source. That was right for the cases that motivated it (FCC Docket 81-413, the Lamarr patent) — those works are *story participants*. But the first agent to work the request queue exposed the failure mode: it created a node for the Bardeen–Brattain patent *merely to have something to cite*, and targeted the transistor's `name` assertion — a claim nobody doubted. At scale this turns every bibliography entry into a book on the map and dilutes citations into decoration.

## Decision
1. **A citation's `source` is a plain identifier by default** — doc-id, URL, ISBN, docket number — stored as data in the citation value `{source, locator}`. Citing NEVER creates a node.
2. **A work becomes a node only when it earns story membership** — the Significance Filter (ADR-0009) applied to works: someone notable authored it (authored-by thread), it enabled/suppressed/unlocked something (the docket pattern), or readers need to navigate to it. Existing story nodes (fcc-81-413, us2292387, usgs-mcs) keep their status.
3. **When a node exists for the source, the citation links it** and the always-connected rule applies (ADR-0038's `documents` thread) — node-existence is an upgrade, never a requirement. The kernel verb already tolerates both (edge laid only `if view.node(source_node)`).
4. **Citations must target the claim being evidenced.** Citing `name` is (almost always) vacuous; the right targets are origin dates, edges/justifications, constraints, validity. Linter L14: a citation whose target assertion is `name` or `aliases` is flagged for review.

## Consequences
- Bibliography scales without map clutter; the map stays a map of *things and story*, not references.
- Agent guidance (MCP instructions): never `propose_node` a WORK_PUBLICATION just to cite it; pass the doc-id as `source_node` directly.
- The us2524035 node created this way is demoted: its vacuous name-citation retracted, replaced by a plain-source citation on a real origin claim. The husk node exposes a design gap — **there is no node tombstone for created-in-error nodes with no merge target** (append-only log, nothing to merge into). Raised as TB-070 / Q-23 rather than solved ad hoc.
