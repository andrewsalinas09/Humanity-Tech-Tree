# Humanity Tech Tree

A knowledge graph of all human technology and culture, where edges are **dependencies** — what needed what to exist. Wikipedia has the articles; this has the causal structure between them.

What it's for:
- **See how technology bootstrapped itself** — iron makes tools, tools make steel, steel makes better tools — with optimization loops that actually terminate.
- **Derive anything from first principles** — trace an iPhone down to natural laws and raw materials, with constraints pruning the paths that are technically true but practically absurd (yes, you *could* build a computer from vacuum tubes; a Switching Speed constraint is why you don't).
- **Crowdsource it safely** — blast-radius permissions, shadow-branch edits, automated circuit breakers, and reputation-staked review, so the graph can be open without being vandalizable.
- **Keep history honest** — fuzzy dates with uncertainty, per-region timelines where knowledge is gained, *lost*, and regained, and epistemic labels from "mainstream fact" to "mythology."

## Status

Design phase, restarted 2026-08. The previous iteration produced ~10,000 lines of design conversation, now distilled into a proper documentation system. There is no build system yet; `Node.cpp` / `AttributeRegistry.h` are schema sketches.

## Where everything is

Start with **[CLAUDE.md](CLAUDE.md)** — the map and working rules (written for AI agent sessions, useful for humans too).

| | |
|---|---|
| [docs/VISION.md](docs/VISION.md) | Why this exists |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current design: graph model, solver semantics, storage, moderation |
| [docs/SCHEMA.md](docs/SCHEMA.md) | **The frozen v1 schema (normative)** |
| [docs/decisions/](docs/decisions/) | 38 architecture decision records — the settled "why"s (normative) |
| [docs/TESTBED.md](docs/TESTBED.md) | 67 edge-case acceptance tests (normative) |
| [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md) | Open design questions (most now resolved → ADRs) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases and current focus |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Domain vocabulary |
| [docs/WORKLOG.md](docs/WORKLOG.md) | Session journal |
| [docs/archive/](docs/archive/) | Original brain-dump and chat digests |
