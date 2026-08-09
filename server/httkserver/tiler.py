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
GHOST_TYPES = {"ASSOCIATION", "SUCCEEDS"}

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
        pa = _lnglat_to_tilepx(a[0], a[1], z, x, y)
        pb = _lnglat_to_tilepx(b[0], b[1], z, x, y)
        if all(p < -EXTENT or p > 2 * EXTENT for p in (pa[0], pb[0])):
            continue
        edges_feats.append({
            "geometry": {"type": "LineString", "coordinates": [list(pa), list(pb)]},
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
def node_card(node_id: str):
    st = _state()
    view = st["view"]
    n = view.node(node_id)
    if n is None:
        return {"missing": node_id}
    r = realizable(view, node_id)
    return {
        "node": n,
        "name": view.field(node_id, "name") or node_id,
        "validity": view.field(node_id, "validity") or "unassessed",
        "cited": _cited(view, node_id),
        "fields": {k[1]: v[1] for k, v in view._fields.items() if k[0] == node_id},
        "edges_in": view.edges_in(node_id),
        "edges_out": view.edges_out(node_id),
        "solve": {"existence": r.existence.value, "fitness": r.fitness.value,
                  "gaps": r.gaps[:20]},
        "position": st["pos"].get(node_id),
    }


@app.get("/solve/{node_id}")
def solve(node_id: str, world_time: float = None, region: str = None):
    view = _state()["view"]
    r = realizable(view, node_id, world_time=world_time, region=region)
    return {"existence": r.existence.value, "fitness": r.fitness.value,
            "gaps": r.gaps, "unfit": r.unfit}


@app.get("/style.json")
def style():
    """MapLibre style: the trust visual language as tokens (docs/COORDINATES.md)."""
    base = os.environ.get("HTT_TILER_URL", "http://localhost:8748")
    cat_colors = ["match", ["get", "category"],
                  "NATURAL_LAW", "#7c5cff", "FORMAL_CONCEPT", "#9d7bff",
                  "MATERIAL", "#8a6d3b", "METHOD_TECHNIQUE", "#2a9d8f",
                  "STANDARD_UNIT", "#457b9d", "CAPABILITY", "#e9c46a",
                  "BIOLOGICAL_ENTITY", "#f4a261", "ORGANIZATION", "#e76f51",
                  "WORK_PUBLICATION", "#b5838d", "#3a86ff"]
    return {
        "version": 8,
        "name": "Humanity Tech Tree",
        "glyphs": "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        "sources": {"httk": {"type": "vector",
                             "tiles": [f"{base}/tiles/{{z}}/{{x}}/{{y}}.mvt"],
                             "minzoom": 0, "maxzoom": 14}},
        "layers": [
            {"id": "bg", "type": "background",
             "paint": {"background-color": "#0b0e14"}},
            {"id": "edges", "type": "line", "source": "httk", "source-layer": "edges",
             "filter": ["!", ["get", "ghost"]],
             "paint": {"line-color": ["case", ["get", "shadowed"], "#39424e",
                                      "#5b8dd9"],
                       "line-width": 1.4, "line-opacity": 0.8,
                       "line-dasharray": ["case", ["get", "shadowed"],
                                          ["literal", [2, 2]], ["literal", [1, 0]]]}},
            {"id": "node-red-ring", "type": "circle", "source": "httk",
             "source-layer": "nodes", "filter": ["!", ["get", "cited"]],
             "paint": {"circle-radius": 11, "circle-color": "rgba(0,0,0,0)",
                       "circle-stroke-color": "#e63946", "circle-stroke-width": 2.5}},
            {"id": "nodes", "type": "circle", "source": "httk", "source-layer": "nodes",
             "paint": {"circle-radius": 7, "circle-color": cat_colors,
                       "circle-opacity": ["match", ["get", "validity"],
                                          "unassessed", 0.35, "hypothetical", 0.5, 1.0],
                       "circle-stroke-color": "#0b0e14", "circle-stroke-width": 1.5}},
            {"id": "labels", "type": "symbol", "source": "httk", "source-layer": "nodes",
             "layout": {"text-field": ["get", "name"], "text-size": 12,
                        "text-offset": [0, 1.4], "text-anchor": "top"},
             "paint": {"text-color": "#dbe4f0", "text-halo-color": "#0b0e14",
                       "text-halo-width": 1.2}},
        ],
        "center": [0, 0], "zoom": 2,
    }
