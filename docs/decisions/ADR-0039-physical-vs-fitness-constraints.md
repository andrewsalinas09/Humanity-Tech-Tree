# ADR-0039: Two constraint classes — PHYSICAL (nature's veto) vs FITNESS (purpose's veto)

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user, restart session ("I CAN'T build transistors with 90% silicon. I CAN build a computer with vacuum tubes... cost-prohibitive vs literally can't. These are two classes")

## Context
Constraints conflated two vetoes. A transistor from 90% silicon does not *function* — timeless physical impossibility. A vacuum-tube computer functions (ENIAC); silver transmission lines conduct; they are vetoed only relative to a *purpose* (pocket-sized, grid-affordable) — context-bound and era-mobile (Napoleon III's aluminum cutlery: more precious than gold then, sandwich wrap now; same physics, flipped fitness). Lumping these poisons the fun questions: "Could Rome build X?" must separate "physics unreachable" from "possible but ruinously costly" — the second is where the interesting history lives.

## Decision
1. **Every AttributeConstraint carries a class:**
   - **PHYSICAL** — violation ⇒ the configuration cannot function, anywhere, ever. Feeds the realizability lattice: certain violation ⇒ contributes PROVEN_UNREALIZABLE.
   - **FITNESS** — violation ⇒ functions but is unfit *for this consumer's purpose*. Prunes the path for this query only; never marks a configuration impossible. Cost, size-for-purpose, power-for-purpose, era-practicality live here — always.
2. **FITNESS is the default; PHYSICAL demands citation.** Impossibility is the strongest claim the graph can make — the burden of proof is on it (ADR-0015: a wrongly-PHYSICAL constraint asserts false impossibility). The class marking is itself a citable, challengeable editorial fact.
3. **Solver output becomes two-axis, each three-valued (ADR-0037):**
   - *Existence:* PROVEN_REALIZABLE / UNKNOWN / PROVEN_UNREALIZABLE — physical constraints only.
   - *Fitness:* FIT / UNFIT(reasons list) / UNKNOWN — per consumer purpose, with the violated fitness constraints as the reasons ("physically possible; unfit: 10⁴× volume, 10³× power").
   - The vacuum-tube iPhone's true verdict is thereby upgraded: not "impossible" but "possible and absurd, here's why" — truer and more fun than a bare prune (refines TB-001's story; ADR-0003's pruning survives as the fitness axis).
4. **Era-mobility is automatic:** fitness thresholds are consumer-purpose facts; the *values* they check (cost, availability) are dated regional facts — so "cost-prohibitive in 1850, cheap in 1950" falls out of ordinary dated attributes with zero new machinery (the aluminum flip).
5. **Counterfactual answers gain the distinction:** "Could Rome build X?" → existence verdict + fitness verdict + both gap lists, separately. "Physically yes, economically no" is a first-class answer.

## Why
Physics is timeless; purposes are contextual. One field for both meant either false impossibilities (silver lines "can't" exist) or laundered absurdities (vacuum iPhones "possible" full stop). Two classes with asymmetric burden of proof match reality's actual structure, keep PROVEN_UNREALIZABLE trustworthy (it now *only* ever means physics), and make the economic texture of history — the entire "why THIS path won" story — queryable instead of flattened.

## Consequences
- SCHEMA: `AttributeConstraint` gains `class: PHYSICAL|FITNESS` (default FITNESS); solver §4 lattice note updated; linter rule: PHYSICAL without citation → flagged.
- Constraint worked example updated (the tube branch's kill is FITNESS at the iPhone seam; the purity kill at the silicon seam is PHYSICAL).
- TB-069 added. TB-001's phrasing refined (prune = fitness verdict, not impossibility).
- Kernel (Phase 2 step 0) implements the two-axis evaluation.
