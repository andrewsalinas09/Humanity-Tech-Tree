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

## Second ruling round (2026-08-09, all pending items resolved)
- **Creation vs optimization (ruled):** "silicon isn't an optimization of quartz — it's something that is PRODUCED. A new thing." Producer processes CREATE via ordinary edges (quartz IS_INGREDIENT_OF silicon; smelter ENABLES silicon) and the producer's rated output rides its edge as an effect (`ENABLES` carries `effect`). OPTIMIZES stays exactly the loop-closer.
- **Nature declares as-found, PER REGION:** quartz can carry purity — and it varies by deposit (TB-077, the Spruce Pine NC case: NC quartz is naturally ultra-pure while other sources need an added optimization step — the map must be able to show why one mine is critical). Regional attribute values join TB-031's RegionalAvailability machinery.
- **Loop grammar confirmed:** internal loop edges are ordinary hard edges ("it's just a node graph that does something — the output is optimization"); process internals consume normal components (grease for the bearing of the motor in the plant, in theory); only the back-edge into the same material is OPTIMIZES.
- **Ops granularity (delegated to Claude, judgment recorded):** first-order reality = **SET as the primary op** (industry publishes RATED outputs: a Siemens plant is rated 9–11N; datasheets, not per-pass physics) **plus relative ops (ADD/MULTIPLY) for genuinely iterative systems** — zone-refining passes, distillation stages, enrichment cascades (the canonical multi-pass loop). Honesty rule: relative ops with an undeclared base evaluate UNKNOWN, never a guess; existence uses the convergence limit under unbounded iterations; pass-count economics deferred to fitness. Multi-loop systems (98→99.9 loop A feeding 99.9→9N loop B) are already expressible as chained OPTIMIZES rungs — nothing fake, experts can always deepen a SET into per-pass detail later.
- **Latch (ruled):** "once it's latched it's latched." The solver tracks FIRST-LIT dates (from process start dates + bootstrap order); timing exists so the graph can say "you could not make this in 1700 because …" — capability persists after a bootstrap path retires; extinction requires an explicit event.
- **Trace at 10k-node depth (ruled by the scale question):** the via-trace is ONE HOP per request — "purity via siemens-process" — and each named process is itself solvable/clickable, so deep routes are explored by expansion, never dumped; Q-26 sheets collapse 100-node factories to single trace entries; gaps bubble the NEAREST missing rung only; the latched capability set is memoized derived data (recompute-on-change, like layout).
- **The keystone (user, closing the round): there are no declarations at all — even nature's.** "ADD/MULTIPLY just need a SET process too. SET is done by the input — mining Spruce Pine SETs the thing." EXTRACTION IS A PROCESS: mining a deposit carries the effect that SETs the as-found value (mining-spruce-pine ⇒ quartz purity SET 0.9999x; a lesser mine SETs lower — regional variation is just different extraction edges, TB-077). Every value in the entire graph therefore originates as a SET effect of some process — extraction at the floor (always lit; its input is the earth), rated producers and optimizers above — and relative ops transform SETs upstream of them. A relative op with no base is not a special honesty rule: it is the standard diagnosis — **a SET-producing process is missing from the graph** — the same vocabulary as the dark loop, and equally bountyable. Fiat is not restricted; it is structurally impossible.
- Remaining before build: verb names (set_effect / add_optimizer) and the Siemens expert-split worked example (feeds Q-26).

## Consequences
- TB-072..075 added. Solver implementation follows the pending rulings, never precedes them.
- Linter idea (TB-074): a material attribute satisfying a demanding constraint with no process on the map is suspicious — review flag, not rejection.
