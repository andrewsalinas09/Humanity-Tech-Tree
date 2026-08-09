# ADR-0047: Admin-gated tombstones for nodes and edges (resolves Q-23)

- **Status:** Accepted
- **Date:** 2026-08-09
- **Source:** user rulings ("let's add a delete ticket but can only be approved by admin"; "also add deletion of edges … it's correct, but eventually this history is no longer useful … HISTORY STILL PRESERVED")

## Context
The log is append-only and nothing is ever deleted (ADR-0011); duplicates heal by merge. Two cases had no exit: a node created in error with NO merge target (TB-070's bibliography husk), and an edge that is *correct but no longer useful* — a coarse link superseded by richer structure (electromagnetism→transistor once the semiconductor-physics chain exists; a hypothetical iPhone→star). Shadowing keeps such edges visible as dashed history; sometimes even that is too much.

## Decision
1. **Tombstones are forward facts**, never log mutations: `node.tombstone {node_id, reason}` and `edge.tombstone {edge_id, reason}`. The view hides a tombstoned node (plus every incident edge) or edge; **as-of reads before the tombstone still see everything** — history preserved by construction, and replay stays order-independent (two-pass, ADR-0023).
2. **Marking is open; approving is admin-only.** `request_deletion(subject_id, reason)` — anyone authenticated, node or edge, reason required — opens a `delete` Decision ticket. Only a user with `is_admin` may resolve it; approval writes the tombstone fact under the admin's identity (blame assigned, ADR-0042). ADR-0015 is why the gate exists: a wrong tombstone hides truth, so the failure mode is centralized in accountable hands.
3. **Tombstone ≠ shadow ≠ retract.** Retract targets assertions (claims); shadow keeps a superseded edge rendered as history; tombstone removes from the live view entirely. Three tools, three intents.
4. Projections (`node_identities`/`edge_identities`) drop tombstoned rows; `rebuild_projections` replays to the same state.
5. **Deletion records are PUBLIC — just not on the main page** (user ruling, same day): tombstones never render on the map, but a public record surface lists every one — what was removed, who marked it, who approved it, the reason, and when — served from the log + ticket trail. Removal is never silent.

## Consequences
- TB-070 → Solved; Q-23 → Resolved. The us2524035 husk was removed by the first real ticket through this flow (agent requested; the agent's own approval was rejected ADMIN; andrew approved).
- `users.is_admin` (migration 005) is the gate; currently andrew.
- Future: un-tombstone (a later forward fact) is trivially compatible if ever ruled needed; tombstone counts could feed reputation slashing (ADR-0013).
