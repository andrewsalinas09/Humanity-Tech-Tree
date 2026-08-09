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
from fastapi import Body, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from httk import Store, View, realizable
from httkdb.factlog import PgFactLog
from httkserver.layout import compute_layout, importance, version_map
from httkserver.service import Service

EXTENT = 4096
BUF = 256                     # tile buffer: geometry clipped server-side (px)
GHOST_TYPES = {"ASSOCIATION", "SUCCEEDS"}
HARD = {"ENABLES", "IS_COMPONENT_OF", "IS_INGREDIENT_OF", "IS_TYPE_OF",
        "IS_REFINEMENT_OF"}


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


_svc = None


def _get_svc():
    global _svc
    if _svc is None:
        _svc = Service(_get_pg())
    return _svc


def _state():
    """Kernel view + layout, cached by log seq (rebuildable derived data)."""
    pg = _get_pg()
    with pg.conn.cursor() as c:
        c.execute("SELECT COALESCE(MAX(seq),0) FROM facts")
        seq = c.fetchone()[0]
    if seq != _cache["seq"]:
        store = Store.load(pg.export_jsonl())
        view = View(store)
        pos, paths = compute_layout(view)
        imp = importance(view)
        vmap = version_map(view)
        # map-style LOD (user ruling): less important books DISAPPEAR as you
        # zoom out — GraphMaps monotone persistence. Versions auto-tuck (they
        # are the deepest tier; manual demerge overrides at any zoom).
        zmin = {}
        for n in pos:
            if n in vmap:
                zmin[n] = 5
            else:
                r = imp.get(n, 0.0)
                zmin[n] = 0 if r >= 0.95 else 2 if r >= 0.6 else 3
        _cache.update(seq=seq, store=store, view=view, pos=pos, paths=paths,
                      imp=imp, vmap=vmap, zmin=zmin)
    return _cache


def _lnglat_to_tilepx(lng, lat, z, tx, ty):
    n = 2 ** z
    xw = (lng + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    yw = (1.0 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return ((xw - tx) * EXTENT, (1 - (yw - ty)) * EXTENT)   # MVT y-up within tile


def _cited(view, node_id):
    """ADR-0038: citations target ASSERTIONS — a node counts as cited when any
    of its claims' authoritative assertions carries a citation."""
    for (subj, field), (aid, _v) in view._fields.items():
        if subj == node_id and view.field(aid, "citation"):
            return True
    return False


@app.get("/changes")
def changes():
    st = _state()
    lngs = [p[0] for p in st["pos"].values()] or [0]
    lats = [p[1] for p in st["pos"].values()] or [0]
    return {"seq": st["seq"],
            "bounds": [min(lngs) - 6, min(lats) - 6, max(lngs) + 6, max(lats) + 6]}


@app.get("/tiles/{z}/{x}/{y}.mvt")
def tile(z: int, x: int, y: int):
    st = _state()
    view, pos = st["view"], st["pos"]
    nodes_feats, edges_feats = [], []
    for n, (lng, lat, layer) in pos.items():
        px, py = _lnglat_to_tilepx(lng, lat, z, x, y)
        if not (0 <= px < EXTENT and 0 <= py < EXTENT):
            continue          # points live in exactly ONE tile (no icon doubling)
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
                "rank": round(st["imp"].get(n, 0.0), 3),   # hub..leaf (airport map)
                "version": n in st["vmap"],                # satellite (collapsible)
                "family": st["vmap"].get(n, (None,))[0] or "",
                "zmin": st["zmin"].get(n, 0),              # map LOD tier
            },
        })
    VERSION_Z = 5                 # the zoom where versions auto-untuck
    for e in view._edges.values():
        a, b = pos.get(e["from"]), pos.get(e["to"])
        if not a or not b:
            continue
        # EDGE LIFTING (ADR-0018 family-bubble semantics, user ruling): while
        # a version is tucked, its edges re-aim at the family root — MIMO
        # plugs visibly into 802.11 instead of floating with a culled edge.
        va = st["vmap"].get(e["from"], (None,))[0]
        vb = st["vmap"].get(e["to"], (None,))[0]
        if (va is None) != (vb is None):
            fam = va or vb
            other = e["to"] if va else e["from"]
            if other != fam and fam in pos and other in pos:
                lp = [(pos[other][0], pos[other][1]), (pos[fam][0], pos[fam][1])]
                if va:                       # keep direction: from → to
                    lp.reverse()
                lpx = [_lnglat_to_tilepx(lng, lat, z, x, y) for lng, lat in lp]
                for run in _clip_polyline(lpx, -BUF, EXTENT + BUF):
                    edges_feats.append({
                        "geometry": {"type": "LineString",
                                     "coordinates": [list(p) for p in run]},
                        "properties": {"edge_id": e["edge_id"] + "~lift",
                                       "type": e["type"],
                                       "qualifier": e.get("qualifier") or "",
                                       "ghost": e["type"] in GHOST_TYPES,
                                       "shadowed": False, "lifted": True,
                                       "rank": round(st["imp"].get(other, 0), 3),
                                       "vfamily": fam,
                                       "ezmin": st["zmin"].get(other, 0),
                                       "zmax": VERSION_Z},
                    })
        # dot's spline (routed AROUND node boxes) in world space, consistent
        # across tiles; straight fallback for satellite/ghost edges. Per-tile
        # convert + Liang-Barsky clip to buffer — no breaks at any zoom
        path = st["paths"].get(e["edge_id"]) or [(a[0], a[1]), (b[0], b[1])]
        px = [_lnglat_to_tilepx(lng, lat, z, x, y) for lng, lat in path]
        for run in _clip_polyline(px, -BUF, EXTENT + BUF):
            edges_feats.append({
                "geometry": {"type": "LineString",
                             "coordinates": [list(p) for p in run]},
                "properties": {"edge_id": e["edge_id"], "type": e["type"],
                               "qualifier": e.get("qualifier") or "",
                               "ghost": e["type"] in GHOST_TYPES,
                               "shadowed": view.is_shadowed(e["edge_id"]),
                               "rank": round(min(st["imp"].get(e["from"], 0),
                                                 st["imp"].get(e["to"], 0)), 3),
                               "vfamily": (st["vmap"].get(e["from"], (None,))[0]
                                           or st["vmap"].get(e["to"], (None,))[0]
                                           or ""),
                               "ezmin": max(st["zmin"].get(e["from"], 0),
                                            st["zmin"].get(e["to"], 0)),
                               # every edge carries the full prop set — an
                               # absent prop makes ["get"] return null and
                               # silently fails boolean filters client-side
                               "lifted": False, "zmax": 99},
            })
    data = mapbox_vector_tile.encode([
        {"name": "edges", "features": edges_feats},
        {"name": "nodes", "features": nodes_feats},
    ], default_options={"extents": EXTENT})
    return Response(content=data, media_type="application/vnd.mapbox-vector-tile")


def _flat_or(x):
    """Top-level OR arms of a requirement expr (['or', a, b] nests left)."""
    if isinstance(x, list) and x and x[0] == "or":
        return _flat_or(x[1]) + _flat_or(x[2])
    return [x]


def _expr_leaves(x, out):
    if isinstance(x, list):
        if x and x[0] == "edge":
            out.append(x[1])
        else:
            for y in x[1:]:
                _expr_leaves(y, out)


def _edge_view(view, e, other_key):
    sd = view.field(e["edge_id"], "start_date") or {}
    return {"edge_id": e["edge_id"], "from": e["from"], "to": e["to"],
            "other": e[other_key],
            "other_name": view.field(e[other_key], "name") or e[other_key],
            "type": e["type"], "qualifier": e.get("qualifier") or "",
            "year": sd.get("year"),
            "justification": view.field(e["edge_id"], "justification"),
            "shadowed": view.is_shadowed(e["edge_id"])}


@app.get("/node/{node_id}")
def node_card(node_id: str, k: int = 9):
    """The card is CHEAP (lazy principle): no solving here — realizability is a
    question you ask (/solve). Neighbor lists are capped (counts + top-k)."""
    st = _state()
    view = st["view"]
    n = view.node(node_id)
    if n is None:
        return {"missing": node_id}
    kinds = HARD | {"OPTIMIZES"}
    ein = [e for e in view.edges_in(node_id, kinds)]
    eout = [e for e in view.edges_out(node_id, kinds)]
    story = ([_edge_view(view, e, "from") for e in view.edges_in(node_id)
              if e["type"] in GHOST_TYPES]
             + [_edge_view(view, e, "to") for e in view.edges_out(node_id)
                if e["type"] in GHOST_TYPES])

    # OR paths (ADR-0017): top-level alternatives of the requirement expr —
    # the card must SHOW the logic, not flatten it into a lying AND-list
    expr = view.field(node_id, "requirement_expr")
    groups = []
    if expr is not None:
        arms = _flat_or(expr)
        if len(arms) > 1:
            for arm in arms:
                leaves = []
                _expr_leaves(arm, leaves)
                groups.append([l for l in leaves if view.edge(l)])
    grouped = {eid: gi for gi, g in enumerate(groups) for eid in g}

    requires = [{**_edge_view(view, e, "from"),
                 "alt_group": grouped.get(e["edge_id"])} for e in ein]

    cites = []
    for (subj, fldname), (aid, _v) in list(view._fields.items()):
        if subj == node_id:
            c = view.field(aid, "citation")
            if c:
                cites.append({"claim": fldname, "source": c.get("source"),
                              "source_name": (view.field(c.get("source"), "name")
                                              or c.get("source")),
                              "locator": c.get("locator")})

    return {
        "node": n,
        "name": view.field(node_id, "name") or node_id,
        "category": n.get("category", "TECHNOLOGY"),
        "description": view.field(node_id, "description"),
        "aliases": view.field(node_id, "aliases", []) or [],
        "validity": view.field(node_id, "validity") or "unassessed",
        "cited": _cited(view, node_id),
        "citations": cites,
        "image_url": view.field(node_id, "image_url"),
        "requires_count": len(ein), "requires": requires[:k],
        "or_group_count": len(groups),
        "enables_count": len(eout),
        "enables": [_edge_view(view, e, "to") for e in eout[:k]],
        "story": story[:k],
        "versions": sorted(
            [{"node_id": v, "year": y} for v, (f, y) in st["vmap"].items()
             if f == node_id], key=lambda r: r["year"]),
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
    # the focus node's own STORY context joins the light-up (1 hop, all edge
    # types) — clicking Hedy Lamarr must light her associations, or people
    # and documents read as unexplained floating books
    for e in view.edges_in(node_id) + view.edges_out(node_id):
        edges.add(e["edge_id"])
        nodes.add(e["from"] if e["to"] == node_id else e["to"])
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


# -- requests (Bounties tab): thin REST proxy over the Service ---------------
@app.get("/requests")
def requests_list(status: str = "open", token: str = "tok-andrew"):
    return _get_svc().list_requests(token, status)


@app.post("/requests")
def requests_post(body: dict = Body(...)):
    token = body.pop("token", "tok-andrew")
    return _get_svc().post_request(token, **body)


@app.post("/requests/{request_id}/endorse")
def requests_endorse(request_id: int, body: dict = Body(default={})):
    return _get_svc().endorse_request(body.get("token", "tok-andrew"), request_id)


@app.post("/requests/{request_id}/reopen")
def requests_reopen(request_id: int, body: dict = Body(...)):
    return _get_svc().reopen_request(body.get("token", "tok-andrew"),
                                     request_id, body.get("reason", ""))


@app.get("/leaderboard")
def leaderboard(token: str = "tok-andrew"):
    return _get_svc().leaderboard(token)


# The trust visual language on a WHITE world (user ruling). Nodes render as
# little books (client-registered images 'book' + 'book-ring'); selection
# dimming rides feature-state 'dim' set by the viewer.
DIM = ["case", ["boolean", ["feature-state", "dim"], False]]

# Edges: FAINT AT REST, VIVID ON FOCUS (user ruling, 2026-08-09 — the
# unanimous production graph-map pattern). 'lit' = in the focused closure;
# 'dim' stays at rest-faint (user: other paths still faint, not gone).
def _edge_state(lit, dim, rest):
    return ["case",
            ["boolean", ["feature-state", "lit"], False], lit,
            ["boolean", ["feature-state", "dim"], False], dim,
            rest]


# Map LOD (user ruling): importance tiers appear as you zoom in, like a map;
# versions are the deepest tier (auto-tuck out, auto-untuck in). The viewer
# re-composes these with the manual demerge override.
SHOW_NODE = ["<=", ["get", "zmin"], ["zoom"]]
SHOW_EDGE = ["all", ["<=", ["get", "ezmin"], ["zoom"]],
             ["any", ["!", ["has", "zmax"]],          # lifted edges retire
              ["<", ["zoom"], ["get", "zmax"]]]]      # once versions unfold


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
            {"id": "edges-ghost", "type": "line", "source": "httk",
             "source-layer": "edges",
             "filter": ["all", ["get", "ghost"], SHOW_EDGE],
             "layout": {"line-cap": "round"},
             # qualifier promotion (user ruling 2026-08-09): authorship /
             # original-work threads get their own sepia voice — storage
             # stays ASSOCIATION+qualifier (the §3.1 escape hatch, visually)
             "paint": {"line-color": ["match", ["get", "qualifier"],
                                      ["authored", "documents", "invented",
                                       "discovered"], "#b07c3a",
                                      "#a99cc0"],
                       "line-width": ["match", ["get", "qualifier"],
                                      ["authored", "documents", "invented",
                                       "discovered"], 1.5, 1.2],
                       "line-opacity": _edge_state(0.75, 0.15, 0.32),
                       "line-dasharray": ["literal", [1, 3]]}},
            {"id": "edges-casing", "type": "line", "source": "httk",
             "source-layer": "edges",
             "filter": ["all", ["!", ["get", "ghost"]], SHOW_EDGE],
             "layout": {"line-cap": "round", "line-join": "round"},
             "paint": {"line-color": "#ffffff",
                       "line-width": ["interpolate", ["linear"], ["zoom"],
                                      2, ["+", 3.2, ["*", 1.8, ["get", "rank"]]],
                                      8, ["+", 4.4, ["*", 2.6, ["get", "rank"]]]],
                       "line-opacity": _edge_state(0.95, 0.0, 0.0)}},
            {"id": "edges", "type": "line", "source": "httk", "source-layer": "edges",
             "filter": ["all", ["!", ["get", "ghost"]], SHOW_EDGE],
             "layout": {"line-cap": "round", "line-join": "round"},
             "paint": {"line-color": ["case",
                                      ["boolean", ["feature-state", "lit"], False],
                                      "#3565b8",
                                      ["case", ["get", "shadowed"], "#c3ccd8",
                                       "#8aa8cf"]],
                       "line-width": ["interpolate", ["linear"], ["zoom"],
                                      2, _edge_state(
                                          ["+", 1.8, ["*", 1.8, ["get", "rank"]]],
                                          0.8,
                                          ["+", 0.8, ["*", 1.2, ["get", "rank"]]]),
                                      8, _edge_state(
                                          ["+", 2.8, ["*", 2.6, ["get", "rank"]]],
                                          1.2,
                                          ["+", 1.4, ["*", 1.8, ["get", "rank"]]])],
                       "line-opacity": _edge_state(
                           0.95, 0.09,
                           ["+", 0.10, ["*", 0.10, ["get", "rank"]]]),
                       "line-dasharray": ["case", ["get", "shadowed"],
                                          ["literal", [2, 2]], ["literal", [1, 0]]]}},
            {"id": "node-ring", "type": "symbol", "source": "httk",
             "source-layer": "nodes",
             "filter": ["all", ["!", ["get", "cited"]], SHOW_NODE],
             "layout": {"icon-image": "book-ring", "icon-size": ["step", ["get", "rank"], 0.75, 0.6, 1.0, 0.95, 1.5],
                        "icon-allow-overlap": True,
                        "symbol-sort-key": ["-", 1, ["get", "rank"]]},
             "paint": {"icon-opacity": [*DIM, 0.3, 1.0]}},
            {"id": "nodes", "type": "symbol", "source": "httk",
             "source-layer": "nodes", "filter": SHOW_NODE,
             "layout": {"icon-image": "book",
                        # versions render as SUB-CARDS: smaller than any tier
                        "icon-size": ["case", ["get", "version"], 0.55,
                                      ["step", ["get", "rank"], 0.75, 0.6, 1.0, 0.95, 1.5]],
                        "icon-allow-overlap": True,
                        "symbol-sort-key": ["-", 1, ["get", "rank"]],  # hubs' labels win
                        "text-field": ["get", "name"],
                        "text-size": ["case", ["get", "version"], 9,
                                      ["step", ["get", "rank"], 10, 0.6, 12, 0.95, 18]],
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
