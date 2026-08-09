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
    """Foundations at the TOP, derived tech descending (user ruling) —
    the iPhone sits at the bottom of everything it rests on."""
    pos = layered_layout(View(_world()))
    assert pos["silicon"][1] > pos["transistor"][1] > pos["cpu"][1] > pos["iphone"][1]
    assert pos["silicon"][2] == 0 and pos["iphone"][2] == 3      # layers


def test_layout_is_deterministic():
    a = layered_layout(View(_world()))
    b = layered_layout(View(_world()))
    assert a == b


def test_versions_cascade_down_right_of_family():
    """Versions are satellites, not citizens (COORDINATES v1.2): they never
    enter the world layers — they hang off the family root as a dated
    waterfall, each generation down and to the right of the last."""
    s = _world()
    s.create_node("wifi")
    s.create_edge("e4", "wifi", "iphone", "ENABLES")
    for v, yr in (("wifi-b", 1999), ("wifi-g", 2003), ("wifi-n", 2009)):
        s.create_node(v)
        s.create_edge(f"r_{v}", v, "wifi", "IS_REFINEMENT_OF")
        s.assert_field(f"r_{v}", "start_date", {"year": float(yr), "unc": 0.5})
    pos = layered_layout(View(s))
    fx, fy, _ = pos["wifi"]
    prev = (fx, fy)
    for v in ("wifi-b", "wifi-g", "wifi-n"):        # date order = cascade order
        x, y, _ = pos[v]
        assert x > prev[0] and y < prev[1], f"{v} not down-right of {prev}"
        prev = (x, y)
    # and the family root itself still lives BELOW its providers' world
    assert pos["wifi"][1] > pos["iphone"][1]


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
