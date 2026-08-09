# ADR-0052: Optimizer capability semantics — cycles, bootstrap, and the end of fiat attributes

- **Status:** Accepted (core semantics) — implementation pending sub-decisions tracked in Q-25
- **Date:** 2026-08-09
- **Source:** the "heart of the tool" conversation (user rulings, quoted below)

## The meaning of OPTIMIZES (user's definition, verbatim reasoning)
"It's there specifically to *break cycles* — that's it. Rule of thumb: if something is there specifically to produce a loop — no matter how many nodes — if the input and the output are the same, it's OPTIMIZES." The OPTIMIZES edge is the **loop-closing back-edge into the material**: `silicon → siemens-process → (OPTIMIZES, effect) → silicon`. However long the internal chain (silicon → TCS synthesis → distillation → CVD → silicon), only the final edge back into the same material is OPTIMIZES. This is why ADR-0006 legalized cycles through OPTIMIZES — that old ruling was waiting for this semantics.

## Declaration doctrine (rules)
1. **Consumers REQUEST**: constraints ride the consumer's edge (`transistor→silicon: purity > 0.99999`, PHYSICAL). A process is an ordinary consumer of its inputs: `silicon→siemens` carries the process's own request (`purity ≥ 0.98`).
2. **Optimizers DECLARE what they deliver**: an effect (`{attr, op, value}`) rides the OPTIMIZES back-edge.
3. **Materials never declare optimized values by fiat.** The seed's `silicon.attrs.purity = 0.999999` with no purification process on the map was a lie; it is retracted (f_00027) and the reopened gap is deliberate. **At scale, no attribute is declared anywhere**: every value is the output of a lit process, chaining down to nature's as-found declarations (quartz as mined). The graph is a map of capabilities and their bootstrap order, not a table of asserted numbers.
4. Grade never splits nodes (ADR-0004 reaffirmed): one silicon; raw is the floor; optimizers define what is reachable above it.

## Solver semantics: least fixpoint with bootstrap and latch (rules)
1. Start from raw/as-found values (nature).
2. Light every process whose input requests are met by currently-achievable values.
3. Lit processes extend the achievable set via their effects.
4. Repeat to fixpoint. **Once lit, latched.**
5. **Self-feeding is legal and true** (Siemens' 6N output trivially satisfies its own ≥98% input; the industry feeds itself). What is forbidden is *lighting without a bootstrap path*: a self-loop no raw chain reaches stays **dark**, and a dark loop is a **diagnosis — "an assumption is missing"** — never grounds for an exclusion hack. (The user explicitly rejected recursion-stack self-exclusion.)
6. Monotone ⇒ unique least fixpoint regardless of evaluation order — ADR-0023's insertion-order independence holds for the capability layer *by construction*.
7. The consumer's route through a process is a **solver trace ("via siemens-process"), never a rewire** — dependencies stay on the material; provisioning paths stay swappable.
8. Competing optimizers = three-valued OR (any lit-and-sufficient ⇒ SAT; none sufficient but some UNKNOWN ⇒ UNKNOWN); each alternative carries pros/cons (price, efficiency) that live on the **fitness** axis, later.
9. Unmet requests are **named, bountyable gaps** ("purity ≥ 6N: no purification process recorded").
10. Time-dependence is essential: before the Siemens process exists, 6N is honestly unattainable; earliest-possible queries (ADR-0025) gain teeth.
11. Iterative loops ("run the loop as many times as needed" — zone refining passes): capability-wise the achievable value is the limit/asymptote; pass-count, throughput, and cost are **economics → fitness axis, deferred** (user: "more for economics than capability").

## The canonical chain (acceptance shape, TB-072)
mining → quartz (as-found) → carbothermic smelting (+carbon, furnace) ⇒ silicon @0.98 → Siemens process (requests ≥0.98) ⇒ silicon @6N → transistor (requests >5N). Bootstrap lights smelter → Siemens → transistor's request met **via** the chain; remove the smelter from history and everything above honestly darkens.

## Explicitly pending (Q-25 — do NOT improvise these)
- Producer-edge bookkeeping: the smelter's input≠output (quartz→silicon), so by the rule of thumb it is NOT an optimizes loop — where does its output effect ride (ENABLES-with-effect vs a declared-baseline convention)?
- SET/ADD/MULTIPLY honesty (relative ops with undeclared base ⇒ UNKNOWN).
- Latch vs history (bootstrap path retires later — does the capability persist?).
- Verb surface (set_effect, add_optimizer) and Result.via trace shape.
- The Siemens expert-split worked example (TCS/distillation/CVD) → feeds Q-26 sheets.

## Consequences
- TB-072..075 added. Solver implementation follows the pending rulings, never precedes them.
- Linter idea (TB-074): a material attribute satisfying a demanding constraint with no process on the map is suspicious — review flag, not rejection.
