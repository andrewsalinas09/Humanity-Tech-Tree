# Worked example: product morphing — Mustang, X, Nokia, Polaroid

Tests TB-036: every way a product can mutate over time, including full rebrand with continuous history and Ship of Theseus. Validates ADR-0022. Principle under test: **the graph never stores "sameness" — identity IS the causal chain.** If a mutation can happen in theory, the graph must express it without a special mechanism.

## The taxonomy of mutation, each with a real case

### 1. Pure rebrand — Twitter → X (2023)
Same node. The change is *data*: `name_history: [{“Twitter”, 2006–2023}, {“X”, 2023–}]`, old name kept in `aliases` for search. Version history (ADR-0011) records who/when/why. No new nodes, no new edges. ("Datsun → Nissan", "Google → Alphabet restructuring" at the org level: same shape.)

### 2. Gradual total replacement (Ship of Theseus) — Ford Mustang gens 1–7, Porsche 911
Family root `Ford Mustang` + generation nodes in the ADR-0018 flat star, dated REPLACED_BY succession. Every generation carries its own component edges; across 60 years literally every part lineage changes (911's air-cooled → water-cooled 1998 = a dated family edge flip).

**The graceful-degradation rule (the Theseus answer):** the family root keeps only claims true family-wide. As reality churns, those claims get date-bounded, widened (ADR-0008), or moved down to generations — until, in the limit, the root holds nothing but name, succession chain, and story edges. **A root that has degraded into a pure identity container is a legal, honest end state**, not a modeling failure. The question "is the 2024 Mustang the same car as the 1964?" is never answered by the graph — it is *displayed*: here is the chain, here is what changed when. Identity is the chain.

### 3. Brand transplant — Mustang Mach-E (2021); Polaroid zombie brand
The Mach-E is an electric crossover on Ford's EV platform — mechanically NOT a refinement of the muscle-car family, and asserting `IS_REFINEMENT_OF` would be wrong information (ADR-0015 violation). What actually moved was the brand. Mechanism (lazy promotion, the lift pattern again):

1. Until a transplant occurs, a brand is just aliases/name data — zero overhead for the 99% of products whose brand never detaches.
2. At the transplant moment, promote: create Brand node `“Mustang” (brand)` with dated `APPLIES_TO` edges → Mustang family (1964–) and → Mach-E family (2021–).
3. Real marketing lineage is story, not mechanics: `Mustang family — GAVE_RISE_TO → Mach-E family` (narrative layer, ignored by dependency traversal like all ghost edges).

Polaroid is the extreme: the brand node outlives the original org and products entirely, its APPLIES_TO edges hopping across unrelated licensee hardware — continuous *name*, zero continuity of anything else, and the graph states exactly that and nothing more.

### 4. Organization pivot — Nokia (paper mill 1865 → rubber → cables → phones → networks)
Orgs are nodes; each era's product families are their own nodes with their own truth; the org's story edges (GAVE_RISE_TO, dated) carry the pivots. No product family pretends continuity with a paper mill.

### 5. Fork — OpenOffice → LibreOffice (2010); Merge — MIGRATED_TO
Fork: two nodes, both `IS_REFINEMENT_OF` (or GAVE_RISE_TO) the common ancestor, which is never deleted (ADR-0011). Merge: `MIGRATED_TO` redirect. Both already-settled machinery.

### 6. Category migration — "the phone becomes a camera that calls"
No node surgery: category claims live in edges and attributes that date and shift; if the migration is real divergence, it's a new family with story edges (case 3's shape without the brand drama).

## What this exercise adds to the schema

- **`name_history`** — dated names on nodes (lazy; empty until a rebrand). `aliases` stay as undated search keys.
- **Brand nodes by lazy promotion** with dated `APPLIES_TO` edges — only when a brand detaches from its original bearer.
- **Root graceful degradation** stated as policy: identity containers are legal end states.

## Graceful-handling checklist (the user's bar: "if it can happen in theory")

| Mutation | Mechanism | New machinery needed? |
|---|---|---|
| Rename/rebrand | name_history + version record | dated names only |
| Ship of Theseus | ADR-0018 star + degradation rule | policy statement only |
| Brand transplant | Brand node promotion + APPLIES_TO | one lazy pattern |
| Zombie brand | same | none |
| Org pivot | story edges | none |
| Fork / merge | ADR-0011 | none |
| Category drift | dated edges/attributes | none |
