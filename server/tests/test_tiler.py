"""Layout + tile contract tests (docs/COORDINATES.md)."""
import mapbox_vector_tile

from httk import Store, View
from httkserver.layout import layered_layout


def _world():
    s = Store()
    for n in ("silicon", "transistor", "cpu", "iphone"):
        s.create_node(n)
    s.create_edge("e1", "silicon", "transistor", "IS_INGREDIENT_OF")
    s.create_edge("e2", "transistor", "cpu", "IS_COMPONENT_OF")
    s.create_edge("e3", "cpu", "iphone", "IS_COMPONENT_OF")
    return s


def test_latitude_is_dependency_altitude():
    """Foundations south, consumers north — the tree grows up the map."""
    pos = layered_layout(View(_world()))
    assert pos["silicon"][1] < pos["transistor"][1] < pos["cpu"][1] < pos["iphone"][1]
    assert pos["silicon"][2] == 0 and pos["iphone"][2] == 3      # layers


def test_layout_is_deterministic():
    a = layered_layout(View(_world()))
    b = layered_layout(View(_world()))
    assert a == b


def test_mvt_roundtrip_carries_trust_props():
    """Encode a tile the tiler's way; decode; the trust language survives."""
    feats = [{"geometry": {"type": "Point", "coordinates": [100, 200]},
              "properties": {"node_id": "iphone", "name": "iPhone",
                             "category": "TECHNOLOGY", "validity": "unassessed",
                             "cited": False, "layer": 3}}]
    data = mapbox_vector_tile.encode(
        [{"name": "nodes", "features": feats}],
        default_options={"extents": 4096})
    decoded = mapbox_vector_tile.decode(data)
    p = decoded["nodes"]["features"][0]["properties"]
    assert p["validity"] == "unassessed" and p["cited"] is False  # red ring + hollow
