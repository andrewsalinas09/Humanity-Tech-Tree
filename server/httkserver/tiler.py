"""The dynamic tiler: the permanent read surface (ADR-0044).

Serves the tile-protocol contract (docs/COORDINATES.md) live from the fact log:
  GET /tiles/{z}/{x}/{y}.mvt   nodes+edges as MVT in Web-Mercator XYZ
  GET /style.json              MapLibre style: three tiers + trust visual language
  GET /node/{id}               node card (fields, edges, kernel solve, trust state)
  GET /changes                 {seq} — poll target for live refresh
  GET /solve/{id}              two-axis three-valued verdict with gaps
The PMTiles bulk pyramid bakes this same contract ahead-of-time at scale.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "backend"))

import mapbox_vector_tile
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from httk import Store, View, realizable
from httkdb.factlog import PgFactLog
from httkserver.layout import layered_layout

EXTENT = 4096
BUF = 256                     # tile buffer: geometry clipped server-side (px)
GHOST_TYPES = {"ASSOCIATION", "SUCCEEDS"}
HARD = {"ENABLES", "IS_COMPONENT_OF", "IS_INGREDIENT_OF", "IS_TYPE_OF",
        "IS_REFINEMENT_OF"}


def _bezier(a, b, n=14):
    """Organic arc between world points: quadratic bezier bowed perpendicular."""
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    dist = (dx * dx + dy * dy) ** 0.5 or 1.0
    bow = min(6.0, dist * 0.12)                 # degrees of sideways bow
    cx, cy = mx - dy / dist * bow, my + dx / dist * bow
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    return pts


def _clip_seg(p, q, lo, hi):
    """Liang-Barsky segment clip to [lo,hi]^2 → clipped (p,q) or None."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for d, a in ((-dx, p[0] - lo), (dx, hi - p[0]), (-dy, p[1] - lo), (dy, hi - p[1])):
        if d == 0:
            if a < 0:
                return None
        else:
            t = a / d
            if d < 0:
                if t > t1:
                    return None
                t0 = max(t0, t)
            else:
                if t < t0:
                    return None
                t1 = min(t1, t)
    return ((p[0] + t0 * dx, p[1] + t0 * dy), (p[0] + t1 * dx, p[1] + t1 * dy))


def _clip_polyline(pts, lo, hi):
    """Clip a polyline to the box; returns runs of consecutive points."""
    runs, cur = [], []
    for i in range(len(pts) - 1):
        seg = _clip_seg(pts[i], pts[i + 1], lo, hi)
        if seg is None:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
            continue
        a, b = seg
        if not cur:
            cur = [a]
        elif cur[-1] != a:
            runs.append(cur)
            cur = [a]
        cur.append(b)
    if len(cur) > 1:
        runs.append(cur)
    return runs

app = FastAPI(title="httk-tiler")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

_pg = None
_cache = {"seq": -1, "view": None, "pos": None, "store": None}


def _get_pg():
    global _pg
    if _pg is None:
        _pg = PgFactLog()
    return _pg


def _state():
    """Kernel view + layout, cached by log seq (rebuildable derived data)."""
    pg = _get_pg()
    with pg.conn.cursor() as c:
        c.execute("SELECT COALESCE(MAX(seq),0) FROM facts")
        seq = c.fetchone()[0]
    if seq != _cache["seq"]:
        store = Store.load(pg.export_jsonl())
        view = View(store)
        _cache.update(seq=seq, store=store, view=view, pos=layered_layout(view))
    return _cache


def _lnglat_to_tilepx(lng, lat, z, tx, ty):
    n = 2 ** z
    xw = (lng + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    yw = (1.0 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return ((xw - tx) * EXTENT, (1 - (yw - ty)) * EXTENT)   # MVT y-up within tile


def _cited(view, node_id):
    return bool(view.field(node_id, "citation") or view.field(node_id, "citations"))


@app.get("/changes")
def changes():
    return {"seq": _state()["seq"]}


@app.get("/tiles/{z}/{x}/{y}.mvt")
def tile(z: int, x: int, y: int):
    st = _state()
    view, pos = st["view"], st["pos"]
    nodes_feats, edges_feats = [], []
    for n, (lng, lat, layer) in pos.items():
        px, py = _lnglat_to_tilepx(lng, lat, z, x, y)
        if not (-EXTENT <= px <= 2 * EXTENT and -EXTENT <= py <= 2 * EXTENT):
            continue                                        # 1-tile buffer for labels
        nd = view.node(n) or {}
        nodes_feats.append({
            "geometry": {"type": "Point", "coordinates": [px, py]},
            "properties": {
                "node_id": n,
                "name": view.field(n, "name") or n,
                "category": nd.get("category", "TECHNOLOGY"),
                "validity": view.field(n, "validity") or "unassessed",
                "cited": _cited(view, n),
                "layer": layer,
            },
        })
    for e in view._edges.values():
        a, b = pos.get(e["from"]), pos.get(e["to"])
        if not a or not b:
            continue
        # organic arc in world space (consistent across tiles), then per-tile
        # convert + Liang-Barsky clip to buffer — no breaks at any zoom
        arc = _bezier((a[0], a[1]), (b[0], b[1]))
        px = [_lnglat_to_tilepx(lng, lat, z, x, y) for lng, lat in arc]
        for run in _clip_polyline(px, -BUF, EXTENT + BUF):
            edges_feats.append({
                "geometry": {"type": "LineString",
                             "coordinates": [list(p) for p in run]},
                "properties": {"edge_id": e["edge_id"], "type": e["type"],
                               "qualifier": e.get("qualifier") or "",
                               "ghost": e["type"] in GHOST_TYPES,
                               "shadowed": view.is_shadowed(e["edge_id"])},
            })
    data = mapbox_vector_tile.encode([
        {"name": "edges", "features": edges_feats},
        {"name": "nodes", "features": nodes_feats},
    ], default_options={"extents": EXTENT})
    return Response(content=data, media_type="application/vnd.mapbox-vector-tile")


@app.get("/node/{node_id}")
def node_card(node_id: str, k: int = 7):
    """The card is CHEAP (lazy principle): no solving here — realizability is a
    question you ask (/solve). Neighbor lists are capped (counts + top-k)."""
    st = _state()
    view = st["view"]
    n = view.node(node_id)
    if n is None:
        return {"missing": node_id}
    ein, eout = view.edges_in(node_id), view.edges_out(node_id)
    return {
        "node": n,
        "name": view.field(node_id, "name") or node_id,
        "validity": view.field(node_id, "validity") or "unassessed",
        "cited": _cited(view, node_id),
        "image_url": view.field(node_id, "image_url"),
        "requires_count": len(ein), "requires": ein[:k],
        "enables_count": len(eout), "enables": eout[:k],
        "position": st["pos"].get(node_id),
    }


@app.get("/closure/{node_id}")
def closure(node_id: str, depth: int = 64, cap: int = 5000):
    """Full dependency closure BOTH ways over hard edges — what focus mode
    lights up 'all the way up and all the way down' (user ruling)."""
    view = _state()["view"]
    nodes, edges = {node_id}, set()

    def walk(start, downstream):
        frontier = {start}
        for _ in range(depth):
            if not frontier or len(nodes) > cap:
                return
            nxt = set()
            for n in frontier:
                es = view.edges_out(n, HARD) if downstream else view.edges_in(n, HARD)
                for e in es:
                    edges.add(e["edge_id"])
                    other = e["to"] if downstream else e["from"]
                    if other not in nodes:
                        nodes.add(other)
                        nxt.add(other)
            frontier = nxt

    walk(node_id, downstream=True)    # everything this enables, transitively
    walk(node_id, downstream=False)   # everything this rests on, transitively
    return {"nodes": sorted(nodes), "edges": sorted(edges), "truncated": len(nodes) > cap}


@app.get("/solve/{node_id}")
def solve(node_id: str, world_time: float = None, region: str = None):
    view = _state()["view"]
    r = realizable(view, node_id, world_time=world_time, region=region)
    return {"existence": r.existence.value, "fitness": r.fitness.value,
            "gaps": r.gaps, "unfit": r.unfit}


@app.get("/search")
def search(q: str):
    """Name/alias search → positions, for the upper-right search box."""
    st = _state()
    view, pos = st["view"], st["pos"]
    ql = q.lower()
    hits = []
    for n in view.nodes():
        names = [n, view.field(n, "name") or ""] + (view.field(n, "aliases", []) or [])
        if any(ql in str(x).lower() for x in names if x):
            p = pos.get(n)
            hits.append({"node_id": n, "name": view.field(n, "name") or n,
                         "lng": p[0] if p else 0, "lat": p[1] if p else 0})
    return {"hits": hits[:10]}


# The trust visual language on a WHITE world (user ruling). Nodes render as
# little books (client-registered images 'book' + 'book-ring'); selection
# dimming rides feature-state 'dim' set by the viewer.
DIM = ["case", ["boolean", ["feature-state", "dim"], False]]


@app.get("/style.json")
def style():
    base = os.environ.get("HTT_TILER_URL", "http://localhost:8748")
    cat_colors = ["match", ["get", "category"],
                  "NATURAL_LAW", "#6d4fd8", "FORMAL_CONCEPT", "#8b5fd6",
                  "MATERIAL", "#8a6d3b", "METHOD_TECHNIQUE", "#1d8a7e",
                  "STANDARD_UNIT", "#3e6f95", "CAPABILITY", "#c99a2e",
                  "BIOLOGICAL_ENTITY", "#d97f3f", "ORGANIZATION", "#cf5f3f",
                  "WORK_PUBLICATION", "#a06a76", "#2f6fd0"]
    return {
        "version": 8,
        "name": "Humanity Tech Tree",
        "glyphs": "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        "sources": {"httk": {"type": "vector",
                             "tiles": [f"{base}/tiles/{{z}}/{{x}}/{{y}}.mvt"],
                             "minzoom": 0, "maxzoom": 14,
                             "promoteId": {"nodes": "node_id",
                                           "edges": "edge_id"}}},
        "layers": [
            {"id": "bg", "type": "background",
             "paint": {"background-color": "#ffffff"}},
            {"id": "edges", "type": "line", "source": "httk", "source-layer": "edges",
             "filter": ["!", ["get", "ghost"]],
             "layout": {"line-cap": "round", "line-join": "round"},
             "paint": {"line-color": ["case", ["get", "shadowed"], "#c3ccd8",
                                      "#8aa8cf"],
                       "line-width": ["interpolate", ["linear"], ["zoom"],
                                      2, 1.2, 8, 2.4],
                       "line-opacity": [*DIM, 0.25, 0.8],
                       "line-dasharray": ["case", ["get", "shadowed"],
                                          ["literal", [2, 2]], ["literal", [1, 0]]]}},
            {"id": "node-ring", "type": "symbol", "source": "httk",
             "source-layer": "nodes", "filter": ["!", ["get", "cited"]],
             "layout": {"icon-image": "book-ring", "icon-size": 1.0,
                        "icon-allow-overlap": True},
             "paint": {"icon-opacity": [*DIM, 0.3, 1.0]}},
            {"id": "nodes", "type": "symbol", "source": "httk",
             "source-layer": "nodes",
             "layout": {"icon-image": "book", "icon-size": 1.0,
                        "icon-allow-overlap": True,
                        "text-field": ["get", "name"], "text-size": 12,
                        "text-offset": [0, 2.1], "text-anchor": "top",
                        "text-optional": True},
             "paint": {"icon-color": cat_colors,
                       "icon-opacity": [*DIM, 0.3,
                                        ["match", ["get", "validity"],
                                         "unassessed", 0.45,
                                         "hypothetical", 0.55, 1.0]],
                       "text-color": "#1b2432",
                       "text-opacity": [*DIM, 0.3, 1.0],
                       "text-halo-color": "#ffffff", "text-halo-width": 1.4}},
        ],
        "center": [0, 20], "zoom": 2,
    }
