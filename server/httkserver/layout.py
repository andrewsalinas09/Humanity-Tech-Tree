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
    return pos
