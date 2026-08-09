"""ADR-0042: nothing defaults to standing; Q1 initial-condition kwargs."""
from httk import Store, View, Tri, realizable
from httk.verbs import StagedFacts, add_component, succeed, associate, refine


def V(s):
    return View(s)


def test_edge_born_complete_in_one_call():
    """Q1: dated + assessed + justified at birth — one atomic staged set."""
    s = Store()
    s.create_node("front_camera"); s.create_node("iphone")
    r = add_component(V(s), whole="iphone", part="front_camera", edge_id="e_fc",
                      start={"year": 2010.5, "unc": 0.1},
                      epistemic="mainstream_fact",
                      justification="iPhone 4 introduced the front camera")
    assert isinstance(r, StagedFacts) and len(r.facts) == 4    # edge + 3 conditions
    r.apply(s)
    v = V(s)
    assert v.field("e_fc", "epistemic") == "mainstream_fact"
    assert v.field("e_fc", "justification")
    assert realizable(v, "iphone", world_time=2007).existence is Tri.VIOL  # dated at birth


def test_unstated_epistemic_is_absent_not_mainstream():
    """No credibility freebies: absence stays absent (renders as 'unassessed')."""
    s = Store()
    s.create_node("aliens"); s.create_node("pyramids")
    add_component(V(s), whole="pyramids", part="aliens_tech", edge_id="e_x").apply(s)
    assert V(s).field("e_x", "epistemic") is None              # zero, honestly


def test_validity_builds_from_zero():
    """A node whose validity nobody asserted confers NO standing (ADR-0042)."""
    s = Store()
    s.append("node.create", {"node_id": "mystery", "category": "TECHNOLOGY"})
    r = realizable(V(s), "mystery")                            # no validity fact
    assert r.existence is Tri.UNKNOWN
    assert any("unassessed" in why for _, why in r.gaps)
    s.assert_field("mystery", "validity", "current_truth")     # standing EARNED
    assert realizable(V(s), "mystery").existence is Tri.SAT


def test_succeed_and_associate_and_refine_compile():
    s = Store()
    for n in ("betamax", "vhs", "sony", "wifi", "wifi6"):
        s.create_node(n)
    succeed(V(s), old="betamax", new="vhs", qualifier="replaced",
            start={"year": 1988, "unc": 1}).apply(s)
    associate(V(s), a="sony", b="betamax", qualifier="custody").apply(s)
    refine(V(s), family="wifi", version="wifi6").apply(s)
    v = V(s)
    assert v.edge("s_betamax_vhs")["qualifier"] == "replaced"
    assert v.edge("a_sony_betamax")["type"] == "ASSOCIATION"
    assert v.edge("r_wifi6_wifi")["type"] == "IS_REFINEMENT_OF"
    # story layer stays solver-invisible: no effect on existence
    assert realizable(v, "vhs").existence is Tri.SAT
