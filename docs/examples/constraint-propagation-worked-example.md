# Worked example: constraint propagation — the two-path Logic Gate

The solver-side companion to the Intercept walkthrough. Question answered: when Logic Gate gains two providers (Transistor OR Vacuum Tube), how do iPhone's needs select the right branch — "how do constraints bubble up properly?" Answer: **they don't bubble up; two flows move in opposite directions and collide at a seam.** (TB-065.)

## The graph after the edits

```
Transistor ──IS_COMPONENT_OF──▶ Logic Gate ──IS_COMPONENT_OF──▶ CPU ──▶ iPhone
Vacuum Tube ─IS_COMPONENT_OF──▶ Logic Gate            (ENIAC ──▶ ...also consumes CPU-era tech)
Logic Gate.requirement_expr = OR(e_transistor, e_tube)     ← wizard asked "alternative or additional?" (L11)
```
Both provider edges are TRUE and permanent (vacuum-tube logic gates ran ENIAC). Nothing is ever deleted to make the iPhone come out right.

## Flow 1 — demand flows DOWN, translating at each hop (ADR-0005)

"You only constrain the things you physically touch":
- **iPhone → CPU edge:** `power_draw < 5 W`, `volume < 10 cm³`. iPhone knows nothing of logic gates.
- **CPU → Logic Gate edge:** the CPU's own translation of its consumers' pressure into its supplier's terms: `switching_speed > 1 MHz`, `power_per_gate < 1 mW`, `volume_per_gate < 1 mm³`.
- **Bag of Rules:** root-attached cross-cutting policies ride the recursion down for demands that skip levels; intermediate nodes stay dumb; strictest-wins on merge.

## Flow 2 — attributes flow UP (ADR-0004)

Provider nodes carry `base_attributes`; optimizer processes stack modifiers; the solver composes virtual instances upward. Vacuum Tube: slow, hot, watt-per-gate, cm³-per-gate. Transistor: the opposite by orders of magnitude.

## The collision — per-query, never stored

Solving `buildable?(iPhone, here, now)` carries the translated demand set down to Logic Gate's OR and evaluates each branch:
- tube branch: `power_per_gate < 1 mW` fails → **no path for this query** → pruned;
- transistor branch: passes → taken.

Ask `buildable?(CPU, USA, 1946)` instead and the tube branch passes — ENIAC's consumer edges carried no such constraints. **Same graph, both answers true.** Pruning is an entailment of (query context + constraints + attributes), computed fresh (ADR-0002/0026); no branch is ever marked "wrong."

## The three pruning mechanisms, in order of preference

1. **Gatekeeper topology — no math (preferred).** iPhone's CPU edge hard-requires *Integrated Circuit*; tubes can make a CPU but can never make an IC, so the branch dies by graph shape alone. Era boundaries encoded topologically (Glossary: gatekeeper node).
2. **Per-unit seam constraints — no aggregation.** Attributes meaningful at the seam itself (`switching_speed`, `power_per_gate`) are comparable without knowing counts. The canonical TB-001 kill. Authoring guidance: "define one or two key properties at the seam where Logic meets Hardware."
3. **Aggregate simulation — deferred.** `total_power = per_gate × N` needs quantities (Q-10, deliberately deferred). The design never depends on this tier; if it ever arrives it slots in as more resolution, not a redesign.

## Absence semantics — the permissive-monotone default (what makes lazy safe; TB-066)

The attribute vocabulary is unbounded data (any name interned on first use, LLM-canonicalized — never a schema list to complete), and nodes declare only load-bearing attributes. That is only safe because absence has defined semantics:

**A constraint referencing an attribute its provider has not declared passes as *presumed-satisfiable*, visibly labeled.** Never a failure, never an error.

- *Why permissive:* failing on unknowns would make incompleteness break the graph (ADR-0015 forbids that); passing-labeled errs exactly as TB-001 errs — technically-true-until-constrained.
- *Why monotone:* declaring an attribute can only prune more, never un-prune — so lazy addition in any order converges (ADR-0023 holds), and no one must pre-enumerate anything.
- *Honest display:* "3 constraints checked, 1 presumed (attribute undeclared)" — the presumption label (ADR-0019 vocabulary) at the attribute level.
- *Convergence engine:* absurd answers trace to the exact seam lacking the exact attribute (ADR-0025 §6 debug harness) → one added fact kills the absurdity class graph-wide. The vacuum-tube iPhone needed ONE attribute at ONE seam; that economy is typical, which is why CPU never needs a billion specs — it needs the handful some consumer actually checks.

## The three-way split, and constraints riding the claim (TB-067)

"iPhone needs a CPU < 3W" involves three distinct objects with three distinct homes:
1. **Attribute name** (`power_draw`) → the registry. Deduplicated by the Q-20-style semantic gate (embedding search over names+descriptions → choose or mint; LLM canonicalization converges synonyms; merge-redirects heal escaped duplicates).
2. **Constraint** (`< 3W`) → the consumer edge (iPhone→CPU, ADR-0005). Never "added to" the provider.
3. **Values** (`= 2.5W`) → provider nodes that actually have the property (A18 declares; the abstract CPU role declares nothing).

**Constraints ride the claim, not the edge instance:** when interposition shadows a constraint-carrying edge (the `< 3W` was authored on iPhone→Transistor before CPU existed), the shadowed edge's constraints remain active demands evaluated along the covering chain (extension of H12: the chain must satisfy the shadowed leaf *and its constraints*). Monotone-safe — retention only prunes. The Intercept wizard additionally triages them toward the most specific correct seam ("relocate `< 3W` to iPhone→CPU?" — LLM proposes, human confirms, the Q-04 shape). Un-relocated is coarse, never wrong; any authoring order converges.

Misplaced *values* need no special rule: a transistor node claiming `power_draw = 3W` is an unsupported fact — L3 verification fails against any real source, challenge, correct. (A `power_per_gate` value on Transistor is legitimate and distinct — the semantic gate keeps seam-level attributes related but separate.)

## Interactions already pinned elsewhere

- OR-branch pruning vs conditionality: a constraint-pruned branch contributes no path, so it cannot witness unconditionality (stress-test HANDLED finding 15 — "path" means solver path, constraints constitutive).
- Constraints only satisfiable *via* an optimizer: composed-mode generation-indexed evaluation (H10).
- Shadowed original edge (Transistor→CPU direct, from the Intercept) is exempt from implicit-AND and satisfied by the chain (H12) — the interposition that created this situation never breaks the expression.
- Full evaluation semantics are Phase 4 (SCHEMA §13.7); the *data* — constraints on edges, attributes on nodes, expressions on consumers — is all captured in v1 now, which is what makes the solver a pure adder later.

## The full trace (what the God-Mode tracer prints)

```text
SOLVE buildable?(iPhone) @ (2026, global)
├─ iPhone.requirement_expr: absent → implicit AND of hard edges
├─ [e_ip] needs CPU · {power_draw < 3W, volume < 10cm³}
│   └─ SOLVE CPU
│      ├─ CPU (abstract role) declares nothing → package check deferred to candidates
│      ├─ [e_lg] needs Logic Gate · {power_per_gate < 1mW, switching_speed > 100MHz}
│      │        ← CPU's AUTHORED translation (chain of responsibility; Q-08 expertise)
│      │   └─ SOLVE Logic Gate: OR(e_transistor, e_vacuum)
│      │      ├─ e_vacuum: power_per_gate ≈ 2W  ✗ < 1mW (certain violation, H2)
│      │      │   ✂ PRUNED — this query only                     [renders red]
│      │      ├─ e_transistor: 100nW ✓, 1GHz ✓
│      │      │   └─ needs Silicon · purity ≥ 99.9999%
│      │      │       → base 99% + Zone-Refining OPTIMIZES modifier stack ✓
│      │      └─ OR satisfied via transistor
│      └─ candidate CPUs (A18: declared power_draw 2.5W ✓, volume ✓) → e_ip satisfied
└─ VERDICT: BUILDABLE — green: iPhone→CPU→LogicGate→Transistor→Silicon; pruned: tubes @ e_lg
```

Honesty notes: the package→per-gate translation is *authored* edge content, never computed; the tube kill compares *declared* values (undeclared would pass presumed-satisfiable per TB-066 — and the absurd green trace becomes the bounty that gets the attribute declared); "riding up" in v1 means checks fire against declared values at each seam (A18's cited 2.5W satisfies the 3W demand) — never gate-count arithmetic (Q-10 deferred); and `buildable?(CPU) @ 1946` passes the tube branch — same graph, opposite selection, both true.

## The takeaway sentence

Demand flows down and translates; attributes flow up and compose; branches die per-query at whichever seam the numbers (or the topology) collide — and the losing branch is never wrong, only unfit for this consumer's purpose, exactly like real engineering.
