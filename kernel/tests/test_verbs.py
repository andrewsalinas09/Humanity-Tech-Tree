"""Verb compilers (ADR-0040/VERBS.md): ignorance cannot break structure."""
from httk import Store, View, Tri, realizable
from httk.verbs import (StagedFacts, Decision, Rejection, add_component,
                        add_ingredient, add_enabler, classify, intercept,
                        exclude, widen, merge, unmerge, set_constraint)


def V(s):
    return View(s)


def test_direction_is_unrepresentable_wrong():
    """Role-named signature: whole/part, not from/to — the edge always points right."""
    s = Store()
    s.create_node("motor"); s.create_node("wire")
    r = add_component(V(s), whole="motor", part="wire")
    assert isinstance(r, StagedFacts)
    r.apply(s)
    e = V(s).edges_in("motor")[0]
    assert e["from"] == "wire" and e["to"] == "motor"          # provider -> consumer


def test_people_are_never_parts_l5():
    s = Store()
    s.create_node("factory"); s.create_node("worker", category="BIOLOGICAL_ENTITY")
    r = add_component(V(s), whole="factory", part="worker")
    assert isinstance(r, Rejection) and r.rule == "L5"


def test_direct_person_enabler_requires_justification_l3():
    s = Store()
    s.create_node("wwi", category="HISTORICAL_EVENT")
    s.create_node("ferdinand", category="BIOLOGICAL_ENTITY")
    r = add_enabler(V(s), enabled="wwi", enabler="ferdinand")
    assert isinstance(r, Rejection) and r.rule == "L3"          # 99.9% default: no
    r = add_enabler(V(s), enabled="wwi", enabler="ferdinand",
                    justification="his assassination IS the causal mechanism (TB-029)")
    assert isinstance(r, StagedFacts) and any("L3" in n for n in r.notes)


def test_l11_same_role_refuses_to_guess_then_compiles_the_or():
    """Silver next to copper: verb returns a Decision, not a silent AND or OR."""
    s = Store()
    for n in ("metal", "copper", "silver", "wire"):
        s.create_node(n)
    s.create_edge("t1", "copper", "metal", "IS_TYPE_OF")
    s.create_edge("t2", "silver", "metal", "IS_TYPE_OF")        # shared ancestor
    add_ingredient(V(s), product="wire", ingredient="copper",
                   edge_id="e_cu").apply(s)
    r = add_ingredient(V(s), product="wire", ingredient="silver")
    assert isinstance(r, Decision)                              # refuses to guess
    assert any(o.get("to") == "e_cu" for o in r.options)        # legal set complete
    # caller resolves: alternative → the OR is compiled mechanically
    r = add_ingredient(V(s), product="wire", ingredient="silver",
                       role={"alternative": "e_cu"}, edge_id="e_ag")
    assert isinstance(r, StagedFacts)
    r.apply(s)
    expr = V(s).field("wire", "requirement_expr")
    assert expr[0] == "or"                                      # TB-068's OR, by verb
    assert realizable(V(s), "wire").existence is Tri.SAT


def test_unrelated_provider_defaults_additional_no_decision():
    s = Store()
    for n in ("motor", "wire", "magnet"):
        s.create_node(n)
    add_component(V(s), whole="motor", part="wire").apply(s)
    r = add_component(V(s), whole="motor", part="magnet")       # no shared ancestor
    assert isinstance(r, StagedFacts)                           # plain AND is safe


def test_classify_rejects_taxonomy_cycle():
    s = Store()
    s.create_node("a"); s.create_node("b")
    classify(V(s), instance="a", type_="b").apply(s)
    r = classify(V(s), instance="b", type_="a")
    assert isinstance(r, Rejection) and r.rule == "B1"


def test_intercept_decision_then_compiles_shadow_never_archive():
    s = Store()
    for n in ("copper", "wire", "motor"):
        s.create_node(n)
    s.create_edge("e500", "copper", "motor", "IS_INGREDIENT_OF")
    r = intercept(V(s), "e500", via="wire")                     # leg types omitted
    assert isinstance(r, Decision) and r.options                # only legal pairs
    r = intercept(V(s), "e500", via="wire",
                  first_leg_type="IS_INGREDIENT_OF", second_leg_type="IS_COMPONENT_OF")
    assert isinstance(r, StagedFacts)
    r.apply(s)
    v = V(s)
    assert v.is_shadowed("e500")                                # shadowed, present
    assert v.edge("e500") is not None                           # NEVER archived
    assert realizable(v, "motor").existence is Tri.SAT          # H12 holds post-verb


def test_exclude_only_inherited_edges():
    s = Store()
    s.create_node("iphone"); s.create_node("iphone1"); s.create_node("gopro")
    s.create_edge("t1", "iphone1", "iphone", "IS_TYPE_OF")
    s.create_edge("e_cam", "front_camera", "iphone", "IS_COMPONENT_OF")
    s.create_edge("e_gp", "lens", "gopro", "IS_COMPONENT_OF")
    r = exclude(V(s), "iphone1", "e_gp", "not mine")            # someone else's edge
    assert isinstance(r, Rejection)
    r = exclude(V(s), "iphone1", "e_cam", "iPhone 1 had no front camera")
    assert isinstance(r, StagedFacts)
    r.apply(s)
    assert realizable(V(s), "iphone1").existence is Tri.SAT     # H11 vacuous, not VIOL


def test_widen_enumerates_ancestors_and_validates():
    s = Store()
    for n in ("thing", "processor", "mobile_proc", "x86", "iphone_proto", "arm"):
        s.create_node(n)
    s.create_edge("ta", "mobile_proc", "processor", "IS_TYPE_OF")
    s.create_edge("tb", "arm", "mobile_proc", "IS_TYPE_OF")
    s.create_edge("tc", "x86", "processor", "IS_TYPE_OF")
    s.create_edge("tp", "processor", "thing", "IS_TYPE_OF")
    s.create_edge("e_req", "mobile_proc", "iphone_proto", "IS_COMPONENT_OF")
    r = widen(V(s), "iphone_proto", "e_req", provider="x86")
    # legal targets computed: common ancestors of mobile_proc and x86 = {processor, thing}
    assert isinstance(r, Decision)
    keys = {o["key"] for o in r.options}
    assert "processor" in keys and "thing" in keys and "arm" not in keys
    r = widen(V(s), "iphone_proto", "e_req", provider="x86", to_ancestor="processor",
              justification="prototype used x86 (TB-017)")
    assert isinstance(r, StagedFacts)
    bad = widen(V(s), "iphone_proto", "e_req", provider="x86", to_ancestor="arm")
    assert isinstance(bad, Rejection)                           # outside the legal set


def test_merge_verb_guards_mobius_and_unmerge_computes_triage():
    s = Store()
    s.create_node("a"); s.create_node("b")
    merge(V(s), "a", "b").apply(s)
    assert isinstance(merge(V(s), "b", "a"), Rejection)         # Möbius at compile time
    s.assert_field("b", "attrs.x", 1)                           # post-merge edit on canonical
    staged, triage = unmerge(s, V(s), "a", "it was two different things")
    staged.apply(s)
    assert V(s).field("a", "migrated_to") is None               # reopened (forward edit)
    assert len(triage) == 1                                     # only POST-merge is a Decision
    assert {o["key"] for o in triage[0].options} == {"keep", "move", "park"}


def test_physical_constraint_demands_citation_l13():
    s = Store()
    s.create_node("si"); s.create_node("tr")
    s.create_edge("e", "si", "tr", "IS_INGREDIENT_OF")
    r = set_constraint(V(s), "e", "purity", "GT", 0.99999, class_="PHYSICAL")
    assert isinstance(r, Rejection) and r.rule == "L13"
    r = set_constraint(V(s), "e", "purity", "GT", 0.99999, class_="PHYSICAL",
                       citation="Sze, Physics of Semiconductor Devices")
    assert isinstance(r, StagedFacts)
