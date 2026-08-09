# Humanity Tech Tree

A knowledge graph of all human technology and culture. Nodes are things (technologies, materials, laws of nature, events, beliefs); edges are dependencies (what needed what to exist). Goals: show how technology bootstrapped itself, let people trace anything to first principles, and crowdsource it safely at scale.

## Current status

**Design phase.** There is no build system and no application code. `Node.cpp` and `AttributeRegistry.h` are schema *sketches* (C++ chosen for expressiveness, not as a committed stack — see Q-02). The real work so far is design thinking, now organized under `docs/`.

## Doc map — where everything lives

| File | Contains | Read when |
|---|---|---|
| `docs/VISION.md` | Why this exists, north-star goals | Starting any session |
| `docs/SCHEMA.md` | **The frozen v1 schema** — fields, physical design, fact log, linters, MCP surface | Any implementation work; supersedes Node.cpp |
| `docs/ARCHITECTURE.md` | Current-state design: data model, systems | Touching schema or design |
| `docs/GLOSSARY.md` | Domain terms (abstract node, logic group, optimization edge…) | A term is unfamiliar |
| `docs/decisions/` | One ADR per settled decision, with the *why* | Before proposing any design change |
| `docs/OPEN-QUESTIONS.md` | Unresolved debates, each with an ID and status | Before designing anything new |
| `docs/TESTBED.md` | Every known edge case (TB-IDs); the design acceptance suite | Before AND after any design change |
| `docs/examples/` | Worked examples validating design patterns (802.11 etc.) | When applying or testing a pattern |
| `docs/ROADMAP.md` | Phases and **current focus** | Starting any session |
| `docs/WORKLOG.md` | Append-only session journal | Resuming after a gap |
| `docs/archive/` | Original raw notes, verbatim | Almost never (history only) |
| `Node.cpp`, `AttributeRegistry.h` | The schema sketch itself | Working on the data model |

## Rules for every agent session

1. **Orient first.** Read this file, `docs/ROADMAP.md` (current focus), and the last 2–3 entries of `docs/WORKLOG.md` before doing anything.
2. **Never re-litigate an Accepted ADR.** If new information genuinely contradicts one, don't argue in chat — write a new ADR that supersedes it (and mark the old one `Superseded by ADR-XXXX`). The user decides.
3. **Every settled design decision becomes an ADR.** If a conversation resolves a debate, capture it in `docs/decisions/` before the session ends, using `docs/decisions/ADR-0000-template.md`. A decision that lives only in chat history is lost.
4. **Every unresolved debate goes to OPEN-QUESTIONS.** If a problem comes up and isn't settled, add it with a Q-ID. When it's later settled, mark it `Resolved → ADR-XXXX`.
4b. **Every edge case goes to TESTBED.md the moment it's raised** — before it's solved. Every design change must be checked against every TB case, and must obey the prime directive (ADR-0015): failure modes may produce incompleteness, never wrongness.
5. **End every session with a WORKLOG entry.** What changed, what was learned, what's next. Use the template at the top of `docs/WORKLOG.md`.
6. **Living docs describe *now*.** `ARCHITECTURE.md`, `GLOSSARY.md`, `ROADMAP.md` are always current-state — update them in place. History belongs in ADRs, the worklog, and git.
7. **Schema changes touch SCHEMA.md** (normative) and, if a decision was involved, an ADR; then sync the derived summaries.
8. **Document authority:** `SCHEMA.md`, ADRs, and `TESTBED.md` are normative; `ARCHITECTURE.md` and `README.md` are derived — on conflict, normative wins. `Node.cpp` is a historical sketch.
