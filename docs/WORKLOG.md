# Worklog

Append-only session journal, newest entry first. Every agent session ends by adding an entry.

Template:
```
## YYYY-MM-DD — short title
**Done:** what actually changed (files, decisions, code)
**Learned:** anything non-obvious discovered
**Next:** the single most useful next step
```

---

## 2026-08-08 — Project restart: documentation system built, old chats distilled
**Done:** Created the full doc system (CLAUDE.md agent contract, docs/: VISION, ARCHITECTURE, GLOSSARY, OPEN-QUESTIONS, ROADMAP, WORKLOG, decisions/ with 14 ADRs, archive/). Digested both Gemini design conversations (~10k lines total) into permanent digests under `docs/archive/digests/` — discovered `Chats/Long chat.pdf` (208 pages) is a print-to-PDF duplicate of `gemini-conversation-2026-01-18-16-05-12.md`, so only the two .md files are canonical sources. Extracted 14 settled decisions into ADRs and 16 open questions into OPEN-QUESTIONS.md.
**Learned:** The old chats settled far more than the README recorded — notably Neo4j + C++ solver split (ADR-0010), state-as-query (ADR-0002), the Manufacturing Test / Lazy Split rules (ADR-0004), the Significance Filter (ADR-0009), and the tracer-bullet build order (ADR-0014). One genuine schema conflict surfaced: Node.cpp's three-level LogicGroup vs. the chat's flatter `alternative_path_id` design (Q-01) — this blocks the solver and should be resolved first.
**Next:** Resolve Q-01 (requirement-logic model), then start Phase 1 tracer bullet (ROADMAP).
