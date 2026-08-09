"""Layout via Graphviz dot → world coordinates per docs/COORDINATES.md.

USER RULING (2026-08-09, docs/research/layout-sota-2026-08.md): dot is the
REFERENCE ENGINE — it teaches us what correct looks like (network-simplex
layering, median+transpose mincross, coordinate assignment, splines routed
around nodes). We will almost certainly hand-implement the pipeline later;
positions are DERIVED data (ADR-0026), so the engine is swappable.

World contract kept: latitude = dependency altitude with FOUNDATIONS AT TOP
(dot rankdir=TB gives this free — sources rank first), longitude = neighbor-
hood corridors (dot's coordinate assignment). Version nodes stay SATELLITES
(timeline cascade off their family root, ~10° slope).
"""
import json
import math
import os
import shutil
import subprocess

from httk.store import HARD_TYPES, TAXONOMY_TYPES

LAT_MIN, LAT_MAX = -78.0, 78.0
LNG_MIN, LNG_MAX = -179.0, 179.0

_DOT_CANDIDATES = (shutil.which("dot"),
                   r"C:\Program Files\Graphviz\bin\dot.exe",
                   "/usr/bin/dot", "/usr/local/bin/dot")
DOT = next((p for p in _DOT_CANDIDATES if p and os.path.exists(p)), "dot")

# degrees per graphviz point: sets on-map density (node pitch ≈ 8° at dev
# scale); capped so tall/wide graphs still fit the world bands
_SCALE = 0.066


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


def _depths(view, nodes, vmap):
    """Longest provider path — kept only as the `layer` display prop."""
    providers = {n: [e["from"] for e in view.edges_in(n, HARD_TYPES | TAXONOMY_TYPES)
                     if view.node(e["from"]) and e["from"] not in vmap]
                 for n in nodes}
    depth = {}

    def d(n, stack=frozenset()):
        if n in depth:
            return depth[n]
        if n in stack:
            return 0
        ps = providers.get(n, [])
        depth[n] = 0 if not ps else 1 + max(d(p, stack | {n}) for p in ps)
        return depth[n]

    for n in nodes:
        d(n)
    return depth


def _dot_quote(s):
    return '"' + s.replace('"', r'\"') + '"'


def _spline_to_polyline(pos_attr, steps=8):
    """Graphviz edge pos (cubic B-spline control points, optional s/e arrow
    points) → sampled polyline in graphviz points."""
    pts, endp, startp = [], None, None
    for tok in pos_attr.split():
        if tok.startswith("e,"):
            endp = tuple(map(float, tok[2:].split(",")))
        elif tok.startswith("s,"):
            startp = tuple(map(float, tok[2:].split(",")))
        else:
            pts.append(tuple(map(float, tok.split(","))))
    if not pts:
        return []
    out = [startp] if startp else []
    out.append(pts[0])
    for i in range(1, len(pts) - 2, 3):    # cubic segments: p0 + triples
        p0 = out[-1]
        p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2]
        for s in range(1, steps + 1):
            t = s / steps
            mt = 1 - t
            out.append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0]
                        + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                        mt**3 * p0[1] + 3 * mt * mt * t * p1[1]
                        + 3 * mt * t * t * p2[1] + t**3 * p3[1]))
    if endp:
        out.append(endp)
    return out


def compute_layout(view):
    """→ (pos, edge_paths).
    pos: {node_id: (lng, lat, layer)}; edge_paths: {edge_id: [(lng, lat), …]}
    (dot's splines, already routed AROUND node boxes — no node-edge overlap
    by construction; the SOTA finding our hand-rolled arcs never had)."""
    vmap = version_map(view)
    nodes = sorted(n for n in view.nodes() if n not in vmap)
    depth = _depths(view, nodes, vmap)

    lines = ["digraph httk {",
             '  rankdir=TB; splines=true; nodesep=1.0; ranksep=1.1;',
             # box ≈ the rendered book icon's world footprint, so splines
             # stop just shy of the visible book (user: "almost touching")
             '  node [shape=box, fixedsize=true, width=0.6, height=0.5,'
             ' label=""];']
    for n in nodes:
        lines.append(f"  {_dot_quote(n)};")
    edge_ids = []
    for n in nodes:
        for e in sorted(view.edges_in(n, None), key=lambda e: e["edge_id"]):
            a, b = e["from"], e["to"]
            if a in vmap or b in vmap or a not in depth or not view.node(a):
                continue
            hard = e["type"] in (HARD_TYPES | TAXONOMY_TYPES)
            attrs = f'id={_dot_quote(e["edge_id"])}'
            if not hard:                   # story edges ride along, never rank
                attrs += ", constraint=false, weight=0"
            lines.append(f"  {_dot_quote(a)} -> {_dot_quote(b)} [{attrs}];")
            edge_ids.append(e["edge_id"])
    lines.append("}")
    src = "\n".join(lines)

    out = subprocess.run([DOT, "-Tjson"], input=src.encode("utf-8"),
                         capture_output=True, check=True, timeout=120)
    doc = json.loads(out.stdout.decode("utf-8"))

    bb = [float(v) for v in doc["bb"].split(",")]     # x0,y0,x1,y1 (y up)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    scale = min(_SCALE,
                (LNG_MAX - LNG_MIN) * 0.9 / max(w, 1),
                (LAT_MAX - LAT_MIN) * 0.9 / max(h, 1))
    cx, cy = bb[0] + w / 2, bb[1] + h / 2

    def world(x, y):
        return ((x - cx) * scale, (y - cy) * scale)

    pos = {}
    for obj in doc.get("objects", []):
        n = obj.get("name")
        if n in depth and "pos" in obj:
            x, y = map(float, obj["pos"].split(","))
            lng, lat = world(x, y)
            pos[n] = (lng, lat, depth[n])

    def _reach(path, center, r=0.55):
        """Extend a path end to r degrees from the node center — edges render
        UNDER icons, so a slight overshoot is invisible and the line reads as
        almost touching the book (user ruling)."""
        (px_, py_), (cx_, cy_) = path[-1], center
        dx, dy = cx_ - px_, cy_ - py_
        d = (dx * dx + dy * dy) ** 0.5
        if d > r:
            path.append((cx_ - dx / d * r, cy_ - dy / d * r))
        return path

    ends = {eid: eid for eid in edge_ids}
    edge_ends = {}
    for n in nodes:
        for e in view.edges_out(n, None):
            if e["edge_id"] in ends:
                edge_ends[e["edge_id"]] = (n, e["to"])
    edge_paths = {}
    for e in doc.get("edges", []):
        eid = e.get("id")
        if eid and "pos" in e:
            pl = _spline_to_polyline(e["pos"])
            if len(pl) >= 2:
                path = [world(x, y) for x, y in pl]
                a, b = edge_ends.get(eid, (None, None))
                if a in pos:
                    path = list(reversed(_reach(list(reversed(path)),
                                                pos[a][:2])))
                if b in pos:
                    path = _reach(path, pos[b][:2])
                edge_paths[eid] = path

    # timeline cascade (user ruling): versions step down-and-right of their
    # family root at ~10°, ordered by date — a waterfall of generations
    by_family = {}
    for v, (fam, year) in vmap.items():
        by_family.setdefault(fam, []).append((year, v))
    for fam, versions in by_family.items():
        if fam not in pos:
            continue
        fx, fy, fl = pos[fam]
        for i, (year, v) in enumerate(sorted(versions)):
            pos[v] = (max(LNG_MIN, min(LNG_MAX, fx + 7.0 + 7.0 * i)),
                      max(LAT_MIN, fy - 2.0 - 1.25 * i), fl)
    return pos, edge_paths


def layered_layout(view):
    """Positions only (compat wrapper over compute_layout)."""
    return compute_layout(view)[0]

# Corridor-country polygons were tried and REJECTED by the user (2026-08-09,
# "it looks bad") — the crude padded-hull version, at least. If countries
# return, do them properly: GMap Voronoi-merge with seas/lakes (git has the
# first attempt).
