"""Layered DAG layout → world coordinates per docs/COORDINATES.md.

Latitude = dependency altitude (foundations south, consumers north).
Longitude = barycenter-ordered domain corridors.
Deterministic full relayout (dev-scale; incremental stability is Q-22).
Positions are DERIVED data (ADR-0026) — rebuildable, never truth.
"""
from httk.store import HARD_TYPES, TAXONOMY_TYPES

LAT_MIN, LAT_MAX = -60.0, 60.0
LNG_MIN, LNG_MAX = -179.0, 179.0


def layered_layout(view):
    """→ {node_id: (lng, lat, layer)}. Layer = longest provider path (hard edges);
    x = barycenter of providers, ties broken by node_id (deterministic)."""
    nodes = view.nodes()
    providers = {n: [e["from"] for e in view.edges_in(n, HARD_TYPES | TAXONOMY_TYPES)
                     if view.node(e["from"])]
                 for n in nodes}

    depth = {}

    def d(n, stack=frozenset()):
        if n in depth:
            return depth[n]
        if n in stack:
            return 0                        # cycle guard (OPTIMIZES excluded anyway)
        ps = providers.get(n, [])
        depth[n] = 0 if not ps else 1 + max(d(p, stack | {n}) for p in ps)
        return depth[n]

    for n in nodes:
        d(n)

    layers = {}
    for n, ly in depth.items():
        layers.setdefault(ly, []).append(n)
    max_layer = max(layers) if layers else 0

    edge_pairs = [(e["from"], e["to"]) for n in nodes
                  for e in view.edges_in(n, HARD_TYPES | TAXONOMY_TYPES)]

    pos = {}
    for ly in sorted(layers):
        # barycenter of providers' x (previous layers already placed)
        def bary(n):
            ps = [pos[p][0] for p in providers.get(n, []) if p in pos]
            return (sum(ps) / len(ps)) if ps else 0.0
        ordered = sorted(layers[ly], key=lambda n: (bary(n), n))
        k = len(ordered)
        # compact world: spread sized to content (zoom-out stays possible;
        # the map grows as corridors multiply, never sprawls preemptively)
        span = min(100.0, 9.0 * max(k, 1))
        for i, n in enumerate(ordered):
            lng = 0.0 if k == 1 else (-span / 2 + span * i / (k - 1))
            # User ruling: foundations at the TOP, derived tech descending —
            # the iPhone sits at the bottom of everything it rests on.
            lat = LAT_MAX if max_layer == 0 else (
                LAT_MAX - (LAT_MAX - LAT_MIN) * ly / max_layer)
            pos[n] = (max(LNG_MIN, min(LNG_MAX, lng)), lat, ly)
    return _relax(pos, edge_pairs)


def _relax(pos, edges, iters=260):
    """Organic settling (user ruling: 'nodes automatically move out of the way').
    Deterministic force relaxation: pairwise repulsion + edge springs + a soft
    anchor to each node's altitude band, so the up/down MEANING survives while
    the rigidity dies. O(n²) per step — fine at dev scale; spatial hashing when
    corridors multiply."""
    ids = sorted(pos)
    P = {n: [pos[n][0], pos[n][1]] for n in ids}
    anchor = {n: pos[n][1] for n in ids}
    for it in range(iters):
        F = {n: [0.0, 0.0] for n in ids}
        for i, a in enumerate(ids):                      # repulsion (bodies!)
            for b in ids[i + 1:]:
                dx, dy = P[a][0] - P[b][0], P[a][1] - P[b][1]
                d2 = dx * dx + dy * dy + 0.01
                if d2 < 625:                             # only near neighbors
                    d = d2 ** 0.5
                    f = 90.0 / d2
                    F[a][0] += f * dx / d; F[a][1] += f * dy / d
                    F[b][0] -= f * dx / d; F[b][1] -= f * dy / d
        for u, v in edges:                               # springs (kinship)
            if u not in P or v not in P:
                continue
            dx, dy = P[v][0] - P[u][0], P[v][1] - P[u][1]
            d = (dx * dx + dy * dy) ** 0.5 + 1e-6
            f = 0.018 * (d - 13.0)
            F[u][0] += f * dx / d; F[u][1] += f * dy / d
            F[v][0] -= f * dx / d; F[v][1] -= f * dy / d
        for n in ids:                                    # altitude still means
            F[n][1] += 0.10 * (anchor[n] - P[n][1])
        step = 0.55 * (1 - it / iters) + 0.04
        for n in ids:
            P[n][0] = max(LNG_MIN, min(LNG_MAX, P[n][0] + step * F[n][0]))
            P[n][1] = max(LAT_MIN, min(LAT_MAX, P[n][1] + step * F[n][1]))
    return {n: (P[n][0], P[n][1], pos[n][2]) for n in ids}
