"""Layered DAG layout → world coordinates per docs/COORDINATES.md.

Latitude = dependency altitude (foundations south, consumers north).
Longitude = barycenter-ordered domain corridors.
Deterministic full relayout (dev-scale; incremental stability is Q-22).
Positions are DERIVED data (ADR-0026) — rebuildable, never truth.
"""
from httk.store import HARD_TYPES, TAXONOMY_TYPES

import math
import zlib

LAT_MIN, LAT_MAX = -78.0, 78.0
LNG_MIN, LNG_MAX = -179.0, 179.0


def importance(view):
    """The airport-map metric (user ruling): hubs vs leaves. Importance =
    degree + transitive dependency mass (the BLAST RADIUS of ADR-0013, live),
    log-normalized to 0..1. Computed, never stored (ADR-0026)."""
    nodes = view.nodes()
    kinds = HARD_TYPES | TAXONOMY_TYPES
    deg = {n: len(view.edges_in(n, kinds)) + len(view.edges_out(n, kinds))
           for n in nodes}
    mass = {}
    for n in nodes:                       # downstream consumers, transitively
        seen, frontier = set(), {n}
        while frontier:
            nxt = set()
            for m in frontier:
                for e in view.edges_out(m, HARD_TYPES):
                    if e["to"] not in seen:
                        seen.add(e["to"])
                        nxt.add(e["to"])
            frontier = nxt
        mass[n] = len(seen)
    raw = {n: deg[n] + 2 * mass[n] for n in nodes}
    mx = max(raw.values(), default=1) or 1
    return {n: math.log1p(raw[n]) / math.log1p(mx) for n in nodes}


def version_map(view):
    """{version_node: (family, year)} from IS_REFINEMENT_OF edges (ADR-0018).
    Versions are SATELLITES of their family (user ruling) — they never enter
    the world layout; they cascade timeline-wise beside their root."""
    out = {}
    for n in view.nodes():
        for e in view.edges_out(n, {"IS_REFINEMENT_OF"}):
            sd = view.field(e["edge_id"], "start_date") or {}
            out[n] = (e["to"], sd.get("year", 0))
            break
    return out


def layered_layout(view):
    """→ {node_id: (lng, lat, layer)}. Layer = longest provider path (hard edges);
    x = barycenter of providers, ties broken by node_id (deterministic).
    Version nodes are excluded and attached as timeline cascades afterward."""
    vmap = version_map(view)
    nodes = [n for n in view.nodes() if n not in vmap]
    providers = {n: [e["from"] for e in view.edges_in(n, HARD_TYPES | TAXONOMY_TYPES)
                     if view.node(e["from"]) and e["from"] not in vmap]
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

    # DETANGLE (user ruling): alternating barycenter sweeps — order every layer
    # by where its neighbors sit in the adjacent layer, downward then upward,
    # repeated. Crossings untwist AND siblings of a hub become adjacent by
    # construction, so similar things group instead of sprawling.
    # Layer-spanning edges get VIRTUAL waypoints (Sugiyama) so an edge passing
    # THROUGH a layer claims a slot there — long diagonals stop slicing
    # blindly across neighborhoods they aren't part of.
    sweep_prov = {n: list(ps) for n, ps in providers.items()}
    virtuals = set()
    springs = []                       # long edges become chains through them
    for n in nodes:
        for p in providers.get(n, []):
            span = depth[n] - depth[p]
            if span > 1:
                prev = p
                for step in range(1, span):
                    v = f"~{p}~{n}~{step}"
                    virtuals.add(v)
                    layers.setdefault(depth[p] + step, []).append(v)
                    sweep_prov[v] = [prev]
                    springs.append((prev, v))
                    prev = v
                springs.append((prev, n))
                sweep_prov[n] = [x for x in sweep_prov[n] if x != p] + [prev]
            else:
                springs.append((p, n))
    consumers = {}
    for n, ps in sweep_prov.items():
        for p in ps:
            consumers.setdefault(p, []).append(n)
    order = {ly: sorted(ns) for ly, ns in layers.items()}
    idx = {n: i for ns in order.values() for i, n in enumerate(ns)}

    def _sweep(neigh):
        for ly in _sweep.dirn:
            def bary(n):
                xs = [idx[m] for m in neigh.get(n, []) if m in idx]
                return (sum(xs) / len(xs)) if xs else idx[n]
            order[ly] = sorted(order[ly], key=lambda n: (bary(n), n))
            for i, n in enumerate(order[ly]):
                idx[n] = i

    for _ in range(8):
        _sweep.dirn = sorted(order)                    # down: follow providers
        _sweep(sweep_prov)
        _sweep.dirn = sorted(order, reverse=True)      # up: follow consumers
        _sweep(consumers)

    order_pairs = [(ns[i], ns[i + 1]) for ns in order.values()
                   for i in range(len(ns) - 1)]

    pos = {}
    for ly in sorted(layers):
        ordered = order[ly]
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
    # virtuals influenced ordering + initial spacing only — the physics runs
    # on real bodies and real edges (virtual bodies fought the springs)
    pos = {n: p for n, p in pos.items() if n not in virtuals}
    real_springs = [(a, b) for a, b in springs
                    if a not in virtuals and b not in virtuals]
    long_edges = [(e["from"], e["to"]) for n in nodes
                  for e in view.edges_in(n, HARD_TYPES | TAXONOMY_TYPES)
                  if depth.get(e["to"], 0) - depth.get(e["from"], 0) > 1
                  and e["from"] in pos]
    order_pairs = [(ns[i], ns[i + 1])
                   for ns in ([x for x in layer if x not in virtuals]
                              for layer in order.values())
                   for i in range(len(ns) - 1)]
    pos = _relax(pos, real_springs + long_edges, importance(view), order_pairs)

    # timeline cascade (user ruling): versions step DOWN AND TO THE RIGHT of
    # their family root, ordered by date — generations reading like a waterfall
    by_family = {}
    for v, (fam, year) in vmap.items():
        by_family.setdefault(fam, []).append((year, v))
    for fam, versions in by_family.items():
        if fam not in pos:
            continue
        fx, fy, fl = pos[fam]
        for i, (year, v) in enumerate(sorted(versions)):
            # gentle ~10° slope (user ruling) — a timeline, not a staircase
            pos[v] = (max(LNG_MIN, min(LNG_MAX, fx + 7.0 + 7.0 * i)),
                      max(LAT_MIN, fy - 2.0 - 1.25 * i), fl)
    return pos


def _relax(pos, edges, imp, order_pairs=(), iters=260):
    """Airport-map settling (user rulings): bodies move out of the way, HUBS
    CARVE TERRITORY (repulsion scales with importance product), LEAVES HUG
    their hub (spring rest length shrinks for low-importance endpoints), and a
    soft altitude anchor keeps the up/down meaning. Deterministic; O(n²) —
    spatial hashing when corridors multiply."""
    ids = sorted(pos)
    P = {n: [pos[n][0], pos[n][1]] for n in ids}
    anchor = {n: pos[n][1] for n in ids}
    w = {n: 0.55 + 0.6 * imp.get(n, 0.0) for n in ids}   # softer hub differential
    for it in range(iters):
        F = {n: [0.0, 0.0] for n in ids}
        for i, a in enumerate(ids):                      # repulsion: AIR (uncrammed)
            for b in ids[i + 1:]:
                dx, dy = P[a][0] - P[b][0], P[a][1] - P[b][1]
                d2 = dx * dx + dy * dy + 0.01
                if d2 < 1.0:      # coincident books stack forever (zero force
                    # direction) — un-stack along a deterministic angle
                    ang = (zlib.crc32(f"{a}|{b}".encode()) % 6283) / 1000.0
                    dx += math.cos(ang); dy += math.sin(ang)
                    d2 = dx * dx + dy * dy + 0.01
                if d2 < 4900:
                    d = d2 ** 0.5
                    f = 1250.0 * w[a] * w[b] / d2
                    F[a][0] += f * dx / d; F[a][1] += f * dy / d
                    F[b][0] -= f * dx / d; F[b][1] -= f * dy / d
        for u, v in edges:                               # springs: leaves hug
            if u not in P or v not in P:
                continue
            dx, dy = P[v][0] - P[u][0], P[v][1] - P[u][1]
            d = (dx * dx + dy * dy) ** 0.5 + 1e-6
            rest = 34.0 + 16.0 * (imp.get(u, 0) + imp.get(v, 0))
            f = 0.02 * (d - rest)
            F[u][0] += f * dx / d; F[u][1] += f * dy / d
            F[v][0] -= f * dx / d; F[v][1] -= f * dy / d
            # TOP-DOWN FLOW (user ruling): dependency chains align into
            # vertical columns — pull edge endpoints toward one longitude
            ax = 0.028 * dx
            F[u][0] += ax; F[v][0] -= ax
        for a, b in order_pairs:      # the sweeps' untangling SURVIVES the
            # physics: within a layer, b stays right of a (no drive-bys that
            # re-cross what the barycenter passes untwisted)
            dx = P[b][0] - P[a][0]
            if dx < 8.0:
                f = 0.09 * (8.0 - dx)
                F[a][0] -= f; F[b][0] += f
        for n in ids:                                    # altitude still means
            F[n][1] += 0.06 * (anchor[n] - P[n][1])
        step = 0.55 * (1 - it / iters) + 0.04
        for n in ids:
            P[n][0] = max(LNG_MIN, min(LNG_MAX, P[n][0] + step * F[n][0]))
            P[n][1] = max(LAT_MIN, min(LAT_MAX, P[n][1] + step * F[n][1]))
    return {n: (P[n][0], P[n][1], pos[n][2]) for n in ids}
