"""ADR-0052 acceptance: the capability fixpoint (TB-072, TB-073, TB-075)."""
from httk import Store, View, realizable
from httk.solve import capabilities, UNBOUNDED
from httk.tri import Tri
from httk.verbs import set_effect, add_optimizer, set_constraint


def _world():
    """TB-072: mining → quartz → smelter ⇒ silicon@0.98 → siemens ⇒ @6N → transistor."""
    s = Store()
    for n in ("mining", "quartz", "smelter", "silicon", "siemens", "transistor"):
        s.create_node(n)
    # extraction SETs the as-found value (the keystone: even nature's values
    # enter through a process; extraction's input is the earth — always lit)
    s.create_edge("e_mine_q", "mining", "quartz", "ENABLES")
    set_effect(View(s), "e_mine_q", "purity", "SET", 0.995).apply(s)
    # producer: quartz feeds the smelter (with the smelter's own request);
    # the smelter ENABLES silicon carrying its rated output
    s.create_edge("e_q_sm", "quartz", "smelter", "IS_INGREDIENT_OF")
    set_constraint(View(s), "e_q_sm", "purity", "GT", 0.9).apply(s)
    s.create_edge("e_sm_si", "smelter", "silicon", "ENABLES")
    set_effect(View(s), "e_sm_si", "purity", "SET", 0.98).apply(s)
    # the loop: silicon in (requesting >=0.98), OPTIMIZES back out at 6N
    s.create_edge("e_si_sie", "silicon", "siemens", "IS_INGREDIENT_OF")
    set_constraint(View(s), "e_si_sie", "purity", "GT", 0.979).apply(s)
    add_optimizer(View(s), target="silicon", process="siemens",
                  attr="purity", op="SET", value=0.999999999).apply(s)
    # the consumer request
    s.create_edge("e_si_tr", "silicon", "transistor", "IS_INGREDIENT_OF")
    set_constraint(View(s), "e_si_tr", "purity", "GT", 0.99999,
                   class_="PHYSICAL", citation="test").apply(s)
    return s


def test_tb072_bootstrap_chain_lights_and_traces():
    v = View(_world())
    cap = capabilities(v)
    assert cap[("quartz", "purity")][0][0] == 0.995      # extraction floor
    assert cap[("silicon", "purity")][-1][0] == 0.999999999  # top rung: siemens
    assert cap[("silicon", "purity")][0][0] == 0.98           # bootstrap rung: smelter
    r = realizable(v, "transistor")
    assert r.existence is Tri.SAT
    routes = {(x["attr"], x["via"]) for x in r.via}
    assert ("purity", "siemens") in routes               # one-hop trace


def test_attribution_credits_the_minimal_rung():
    """The smelter bootstrapped Siemens — the trace must SAY so: Siemens' own
    input request (>0.979) is credited to the smelter's 0.98 rung, never to
    Siemens itself (no self-crediting loops in traces)."""
    v = View(_world())
    r = realizable(v, "siemens")
    assert r.existence is Tri.SAT
    hit = next(x for x in r.via if x["edge"] == "e_si_sie")
    assert hit["via"] == "smelter" and hit["value"] == 0.98


def test_tb073_no_bootstrap_stays_dark_with_named_gap():
    s = _world()
    v = View(s)
    # sever the bootstrap: the smelter's rated output is retracted
    aid = v.field_assertion("e_sm_si", "effect")
    s.retract(aid)
    v = View(s)
    cap = capabilities(v)
    # siemens self-feeds in principle but nothing bootstraps silicon: dark
    assert ("silicon", "purity") not in cap
    r = realizable(v, "transistor")
    assert r.existence is Tri.UNKNOWN                    # never VIOL — incomplete
    assert any("purity" in why for _, why in r.gaps)


def test_tb072_insufficient_rung_names_nearest():
    s = _world()
    v = View(s)
    # weaken siemens to below the transistor's request
    aid = v.field_assertion("o_siemens_silicon", "effect")
    s.retract(aid)
    set_effect(View(s), "o_siemens_silicon", "purity", "SET", 0.999).apply(s)
    r = realizable(View(s), "transistor")
    assert r.existence is Tri.UNKNOWN
    assert any("short of" in why and "0.999" in why for _, why in r.gaps)


def test_tb075_relative_op_unbounded_with_base_dark_without():
    s = _world()
    # zone refining: MULTIPLY rides on top of the smelter's SET base
    s.create_node("zone-refining")
    s.create_edge("e_si_zr", "silicon", "zone-refining", "IS_INGREDIENT_OF")
    add_optimizer(View(s), target="silicon", process="zone-refining",
                  attr="purity", op="MULTIPLY", value=0.1).apply(s)
    cap = capabilities(View(s))
    assert cap[("silicon", "purity")][-1][0] is UNBOUNDED  # iterate as needed
    r = realizable(View(s), "transistor")
    assert r.existence is Tri.SAT
    # without ANY set (fresh world): relative op alone stays dark
    s2 = Store()
    for n in ("m", "zr"):
        s2.create_node(n)
    s2.create_edge("e1", "m", "zr", "IS_INGREDIENT_OF")
    add_optimizer(View(s2), target="m", process="zr",
                  attr="purity", op="MULTIPLY", value=0.1).apply(s2)
    assert ("m", "purity") not in capabilities(View(s2))  # keystone: SET missing
