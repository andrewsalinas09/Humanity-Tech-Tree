# The Reference Semantics Kernel

**This is the executable specification of `docs/SCHEMA.md`** — Phase 2 step 0 (external review item #5). It is deliberately small, clear Python: the point is that there is exactly ONE reading of the frozen schema's semantics, and it runs. Any production implementation (solver language still open, Q-16) proves itself by passing this kernel's test fixtures.

**Not the product.** No database, no MCP, no UI, no performance goals. Facts live in memory / JSONL. Citations, verification ladder, confidence, and moderation are out of scope for step 0 (they are event-plumbing over the same store, not solver semantics).

## What it implements

| Module | Semantics |
|---|---|
| `httk/tri.py` | Three-valued logic: SAT / VIOL / UNKNOWN with Kleene composition (ADR-0037) |
| `httk/store.py` | Append-only assertions with stable IDs; identity vs assertion split (ADR-0038); as-of record-time resolution (ADR-0034); JSONL fact log round-trip; merge-redirect walk with cycle breaker (H4) |
| `httk/dates.py` | Decimal-year intervals; certain-violation-only comparisons (H2/ADR-0037) |
| `httk/solve.py` | Requirement-expression evaluation (ADR-0017) with exclusion-vacuity (H11), shadow exemption (H12), claim-equivalence implicit-AND (H13), taxonomy-DAG inheritance (H17/ADR-0019); two-axis realizability — existence × fitness (ADR-0039) — with PHYSICAL/FITNESS constraint classes, undeclared-attribute → UNKNOWN (TB-066), OPTIMIZES existence-skip (ADR-0006), possibility masks for works/people (ADR-0025), hypothetical-leaf guard (TB-041), regional availability with existential composition (H3), hard-cycle detection (B1), and the entailment-vs-fact contradiction detector (TB-042) |

## Reference rulings the kernel pins (where prose allowed latitude)

- **OR over two axes:** an OR selects its best branch ordered by existence then fitness (SAT > UNKNOWN > VIOL); the result is that branch's pair. Prevents "exists via branch A, fit via branch B" chimeras.
- **Date checks under ADR-0037:** certainly-outside → VIOL; overlap → UNKNOWN (ADR-0037 supersedes H2's "overlap passes" with the honest value); certainly-inside → SAT.
- **Shadowed-edge constraints (TB-067):** evaluated against the shadowed edge's own provider (same provider, so the demand survives verbatim); existence satisfied via the covering chain (H12).
- **Record time** is a monotone integer sequence (logical clock); wall-clock timestamps are presentation.

## Run

```
cd kernel
python -m pytest tests/ -q
```
