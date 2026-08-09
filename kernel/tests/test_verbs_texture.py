"""The texture verbs: every schema field authorable (user ruling)."""
from httk import Store, View, Tri, realizable, available
from httk.verbs import (StagedFacts, Rejection, add_component, set_attribute,
                        add_time_segment, date_edge, add_iteration, lift_iteration,
                        rename, add_alias, reclassify, retract_assertion,
                        mark_shadowed, add_alternative_bundle, move_assertion,
                        park_assertion, flag, set_constraint)


def V(s):
    return View(s)


def test_set_attribute_feeds_the_solver():
    s = Store()
    s.create_node("tube"); s.create_node("gate")
    s.create_edge("e_v", "tube", "gate", "IS_COMPONENT_OF")
    set_constraint(V(s), "e_v", "power_per_gate", "LT", 0.001).apply(s)
    assert realizable(V(s), "gate").fitness is Tri.UNKNOWN     # undeclared → UNKNOWN
    set_attribute(V(s), "tube", "power_per_gate", 2.0).apply(s)
    assert realizable(V(s), "gate").fitness is Tri.VIOL        # declared → decided


def test_timeline_verb_and_h3_overlap_flag():
    s = Store()
    s.create_node("concrete")
    add_time_segment(V(s), "concrete", "geo:europe",
                     {"status": "ACTIVE", "start": -200, "end": 476}).apply(s)
    add_time_segment(V(s), "concrete", "geo:europe",
                     {"status": "LOST", "start": 476, "end": 1414}).apply(s)
    assert available(V(s), "concrete", "geo:europe", 1000)[0] is Tri.VIOL
    r = add_time_segment(V(s), "concrete", "geo:europe",
                         {"status": "ACTIVE", "start": 1200})   # overlaps the LOST span
    assert any("region-decomposition" in n for n in r.notes)    # flagged, not rejected


def test_iteration_record_then_lift():
    """802.11j: data record today, node tomorrow — the ADR-0018 lifting debt paid."""
    s = Store()
    s.create_node("wifi"); s.create_node("ofdm")
    add_iteration(V(s), "wifi", {"name": "802.11j", "year": 2004,
                                 "key_feature": "Japan bands"}).apply(s)
    assert isinstance(add_iteration(V(s), "wifi", {"name": "802.11j", "year": 2004}),
                      Rejection)                                # no duplicate records
    add_iteration(V(s), "wifi", {"name": "802.11g", "year": 2003,
                                 "tech_ids": ["ofdm"]}).apply(s)
    lift_iteration(V(s), "wifi", "802.11g", node_id="wifi-g").apply(s)
    v = V(s)
    assert v.node("wifi-g") is not None                         # record became a node
    assert any(e["from"] == "wifi-g" and e["to"] == "wifi"
               for e in v.edges_out("wifi-g"))                  # IS_REFINEMENT_OF star
    assert any(e["from"] == "ofdm" for e in v.edges_in("wifi-g"))  # tech link lifted
    names = [r["name"] for r in v.field("wifi", "iterations")]
    assert names == ["802.11j"]                                 # lifted record removed
    assert realizable(v, "wifi-g").existence is Tri.SAT


def test_rename_builds_dated_history_and_alias():
    s = Store()
    s.create_node("twitter"); s.assert_field("twitter", "name", "Twitter")
    rename(V(s), "twitter", "X", year=2023).apply(s)
    v = V(s)
    assert v.field("twitter", "name") == "X"
    assert v.field("twitter", "name_history")[-1] == {"name": "X", "start": 2023}
    assert "Twitter" in v.field("twitter", "aliases")           # old name searchable
    add_alias(V(s), "twitter", "the everything app").apply(s)
    assert "the everything app" in V(s).field("twitter", "aliases")


def test_reclassify_is_correctable_and_downstream_checks_use_it():
    s = Store()
    s.create_node("acme", category="TECHNOLOGY")                # miscategorized
    s.create_node("factory")
    assert isinstance(add_component(V(s), whole="factory", part="acme"), StagedFacts)
    r = reclassify(V(s), "acme", "ORGANIZATION", "it's a company, not a machine")
    r.apply(s)
    assert V(s).node("acme")["category"] == "ORGANIZATION"      # the category-field fix
    assert isinstance(add_component(V(s), whole="factory", part="acme"), Rejection)


def test_bundle_alternative_makes_tb021_authorable():
    """OR(platinum, AND(palladium, heat)) — by verbs, not raw expression editing."""
    s = Store()
    s.create_node("pd"); s.create_node("heat"); s.create_node("widget")
    s.create_edge("e_pt", "platinum", "widget", "IS_INGREDIENT_OF")   # stub provider
    r = add_alternative_bundle(V(s), "widget", "e_pt",
                               [{"provider": "pd", "type": "IS_INGREDIENT_OF"},
                                {"provider": "heat", "type": "ENABLES"}])
    assert isinstance(r, StagedFacts)
    r.apply(s)
    expr = V(s).field("widget", "requirement_expr")
    assert expr[0] == "or" and expr[2][0] == "and"              # the TB-021 shape
    assert realizable(V(s), "widget").existence is Tri.SAT      # proven via the bundle


def test_mark_shadowed_resolves_l8():
    s = Store()
    for n in ("iphone", "battery", "lithium"):
        s.create_node(n)
    s.create_edge("e_direct", "lithium", "iphone", "IS_INGREDIENT_OF")
    s.create_edge("e_a", "lithium", "battery", "IS_INGREDIENT_OF")
    s.create_edge("e_b", "battery", "iphone", "IS_COMPONENT_OF")
    assert isinstance(mark_shadowed(V(s), "e_direct", ["e_a", "ghost"]), Rejection)
    mark_shadowed(V(s), "e_direct", ["e_a", "e_b"], "TB-025 cleanup").apply(s)
    v = V(s)
    assert v.is_shadowed("e_direct") and v.edge("e_direct")     # masked, never deleted
    assert realizable(v, "iphone").existence is Tri.SAT


def test_move_and_park_close_the_unmerge_triage():
    s = Store()
    s.create_node("metal"); s.create_node("a"); s.create_node("b")
    s.create_edge("ta", "a", "metal", "IS_TYPE_OF")
    aid = s.assert_field("b", "attrs.melting_point", 1811)      # landed on wrong node
    move_assertion(s, V(s), aid, "a", "belongs to a").apply(s)
    v = V(s)
    assert v.field("a", "attrs.melting_point") == 1811
    assert v.field("b", "attrs.melting_point") is None          # retracted, in history
    aid2 = s.assert_field("a", "attrs.color", "gray")
    park_assertion(s, V(s), aid2, "metal", "ambiguous which metal").apply(s)
    v = V(s)
    assert v.field("metal", "attrs.color") == "gray"            # coarser-but-true home
    assert any(f["kind"] == "parked-claim" for f in v.field("metal", "flags"))


def test_flag_and_retract():
    s = Store()
    s.create_node("vacuum_tube_iphone_path")
    flag(V(s), "vacuum_tube_iphone_path",
         "absurd trace: missing switching-speed constraint").apply(s)
    assert V(s).field("vacuum_tube_iphone_path", "flags")       # the bounty exists
    aid = s.assert_field("vacuum_tube_iphone_path", "attrs.junk", 1)
    retract_assertion(V(s), aid, "spurious").apply(s)
    assert V(s).field("vacuum_tube_iphone_path", "attrs.junk") is None


def test_date_edge():
    s = Store()
    s.create_node("front_camera"); s.create_node("iphone")
    s.create_edge("e_fc", "front_camera", "iphone", "IS_COMPONENT_OF")
    date_edge(V(s), "e_fc", start={"year": 2010.5, "unc": 0.1}).apply(s)
    assert realizable(V(s), "iphone", world_time=2007).existence is Tri.VIOL
    assert realizable(V(s), "iphone", world_time=2015).existence is Tri.SAT
