# ADR-0054: The incremental invariant — the graph is a dynamic program

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user ruling ("a lot of this is only possible if we start doing it. It's a dynamic programming problem, not O(N²) — you assume the latest thing you add needs to be checked, but not everything else, because it was checked already")

## Decision
1. **Check at insert, never re-audit.** Every new fact is validated against the already-validated whole at the moment it arrives (the gate, the breakers, the dupe checks, the endpoint guards). The standing graph is trusted *because every piece passed its check when it entered* — there is no future batch audit, and none is ever needed. Total cost: O(new × check), never O(all²).
2. **The fact log's `seq` is the DP axis.** Every derived computation checkpoints at a seq and processes only the delta: embeddings (hash-gated — already incremental), the kernel view cache (seq-keyed — already incremental), reputation (recompute-on-event), linters and layout (currently full re-scan at dev scale; their upgrade path is a seq cursor — "examine only neighborhoods touched since last run" — noted, not urgent).
3. **ADR-0023 is the correctness condition.** Incremental processing is only *legal* because results are insertion-order independent: processing deltas in arrival order provably converges to the same answer as any batch recomputation. Order-independence wasn't just editorial hygiene — it is what licenses the DP.
4. **Latching is memoization.** ADR-0052's "once lit, latched" is this principle inside the solver: capabilities, once established, are cached truths that new work builds on, not re-derivations.
5. **Verification is monotone the same way**: a verified claim stays at its rung until *challenged* — there is no re-verification sweep; only new claims enter the L1 queue, and demotion is event-driven (ADR-0032), not scan-driven.
6. **The start-now corollary** (the user's opening clause): the validated core compounds daily and can never be reconstructed by a future batch effort at feasible cost. Every day of correct operation is capital; breaking the invariant (letting unchecked content in "to fix later") destroys it retroactively. This is why the gates are unskippable by construction, not by policy.

## Why
At a billion nodes, any O(all²) obligation — pairwise dedup sweeps, full re-verification, global relayout on every edit — is death. The architecture survives scale iff every obligation is O(delta) against memoized state. Most of the system already has this shape; naming the invariant makes it a review criterion: **any proposed mechanism that requires revisiting the checked past is wrong by default.**

## Consequences
- Review question for every future design: "what does this cost per NEW fact?" — if the answer mentions the whole graph, redesign.
- Known dev-scale exceptions with recorded upgrade paths: linter full scans (→ seq cursor), full relayout (Q-22 → DynaDAG-style incremental), Python KNN (→ pgvector HNSW).
