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

## 2026-08-09 — Re-scope: tree before solver; test bed established; prime directive named
**Done:** Created `docs/TESTBED.md` with 30 edge cases (TB-001..030) as the permanent design acceptance suite — including new cases from this session: GoPro GPS gap (TB-006), CPU single-node fan-out (TB-013), 802.11/TSF and Thunderbolt version families (TB-014/015), ASML high-fan-in authoring (TB-027). Wrote ADR-0015 ("never wrong, only incomplete" as the prime directive) and ADR-0016 (tree-first build order — supersedes ADR-0014; solver demoted to Phase 4, community correctness layer promoted to core product). Rewrote ROADMAP accordingly. Added Q-17 (storage engine decision reopened — Neo4j choice came from old-LLM era and predates the TB-scale estimate), Q-18 (version families/fan-out), Q-19 (high-fan-in authoring UX). Wired the test bed into CLAUDE.md rules.
**Learned:** User's framing: the solver was always an added feature — the browsable tree + community correctness (LLM triage + voting, citations) IS the product. Scale ambition: tens of millions–billions of nodes, possibly TBs. Design-on-paper-first is deliberate: schema mistakes at that scale are near-irreversible, hence the test bed as the forcing function.
**Next:** Work TESTBED OPEN cases with the user, starting Q-01 (logic model, TB-021) and Q-18 (802.11/Thunderbolt/CPU worked examples).

## 2026-08-08 — Project restart: documentation system built, old chats distilled
**Done:** Created the full doc system (CLAUDE.md agent contract, docs/: VISION, ARCHITECTURE, GLOSSARY, OPEN-QUESTIONS, ROADMAP, WORKLOG, decisions/ with 14 ADRs, archive/). Digested both Gemini design conversations (~10k lines total) into permanent digests under `docs/archive/digests/` — discovered `Chats/Long chat.pdf` (208 pages) is a print-to-PDF duplicate of `gemini-conversation-2026-01-18-16-05-12.md`, so only the two .md files are canonical sources. Extracted 14 settled decisions into ADRs and 16 open questions into OPEN-QUESTIONS.md.
**Learned:** The old chats settled far more than the README recorded — notably Neo4j + C++ solver split (ADR-0010), state-as-query (ADR-0002), the Manufacturing Test / Lazy Split rules (ADR-0004), the Significance Filter (ADR-0009), and the tracer-bullet build order (ADR-0014). One genuine schema conflict surfaced: Node.cpp's three-level LogicGroup vs. the chat's flatter `alternative_path_id` design (Q-01) — this blocks the solver and should be resolved first.
**Next:** Resolve Q-01 (requirement-logic model), then start Phase 1 tracer bullet (ROADMAP).
