"""TESTBED cases as executable fixtures — the acceptance suite for the kernel.

Each test names the TESTBED case / ADR it encodes. If a test here disagrees with
docs/SCHEMA.md or an ADR, the docs win and the kernel has a bug.
"""
import pytest

from httk import (Tri, t_and, t_or, t_not, Store, View, BreakerViolation,
                  Interval, cmp_certain, realizable, effective_expr, available,
                  find_hard_cycles, contradictions)
from httk.dates import point_in_span


def solve(store, node, **kw):
    return realizable(View(store), node, **kw)


# ---------------------------------------------------------------- ADR-0037 ---

def test_kleene_algebra():
    U, S_, V_ = Tri.UNKNOWN, Tri.SAT, Tri.VIOL
    assert t_and([S_, S_]) is S_
    assert t_and([S_, U]) is U            # UNKNOWN dominates TRUE in AND
    assert t_and([U, V_]) is V_           # VIOL dominates everything in AND
    assert t_or([V_, U]) is U             # UNKNOWN dominates FALSE in OR
    assert t_or([U, S_]) is S_            # SAT dominates everything in OR
    assert t_not(U) is U
    assert t_and([]) is S_                # empty AND = nothing demanded
    assert t_or([]) is None               # empty OR = vacuous (H11), not a value


# --------------------------------------------------- TB-001 / TB-065 / TB-069

def _gate_world(s):
    s.create_node("silicon"); s.assert_field("silicon", "attrs.purity", 0.999999)
    s.create_node("transistor")
    s.create_edge("e_si", "silicon", "transistor", "IS_INGREDIENT_OF")
    s.assert_field("e_si", "constraints",
                   [{"attr": "purity", "op": "GT", "value": 0.99999, "class": "PHYSICAL"}])
    s.create_node("tube"); s.assert_field("tube", "attrs.power_per_gate", 2.0)
    s.assert_field("transistor", "attrs.power_per_gate", 1e-7)
    s.create_node("gate")
    s.create_edge("e_t", "transistor", "gate", "IS_COMPONENT_OF")
    s.create_edge("e_v", "tube", "gate", "IS_COMPONENT_OF")
    return s


def test_tb069_two_axes_vacuum_vs_silicon():
    """iPhone-class demand: tube branch is UNFIT (works, absurd); silicon branch wins."""
    s = _gate_world(Store())
    per_gate = [{"attr": "power_per_gate", "op": "LT", "value": 0.001}]  # FITNESS default
    s.assert_field("e_t", "constraints", per_gate)
    s.assert_field("e_v", "constraints", per_gate)
    s.assert_field("gate", "requirement_expr", ("or", ("edge", "e_t"), ("edge", "e_v")))
    r = solve(s, "gate")
    assert r.existence is Tri.SAT and r.fitness is Tri.SAT  # transistor branch chosen

    # tube alone: EXISTS (ENIAC!) but unfit — never "impossible" (ADR-0039)
    s.assert_field("gate", "requirement_expr", ("edge", "e_v"))
    r = solve(s, "gate")
    assert r.existence is Tri.SAT and r.fitness is Tri.VIOL
    assert r.unfit                                            # reasons list populated


def test_tb069_physical_kill_is_existence():
    """90% silicon: the transistor does not FUNCTION — existence VIOL, not fitness."""
    s = _gate_world(Store())
    s.assert_field("silicon", "attrs.purity", 0.90)           # supersedes (ADR-0011)
    r = solve(s, "transistor")
    assert r.existence is Tri.VIOL


def test_tb065_per_query_pruning():
    """ENIAC-1946: same tube, no fitness demand — passes. Same graph, both answers true."""
    s = _gate_world(Store())
    s.assert_field("gate", "requirement_expr", ("edge", "e_v"))  # no constraints on e_v
    r = solve(s, "gate")
    assert r.existence is Tri.SAT and r.fitness is Tri.SAT


# ------------------------------------------------------------------- TB-066 --

def test_tb066_undeclared_attribute_is_unknown_never_yes():
    s = Store()
    s.create_node("steel")                                    # tensile strength undeclared
    s.create_node("bridge")
    s.create_edge("e_s", "steel", "bridge", "IS_INGREDIENT_OF")
    s.assert_field("e_s", "constraints",
                   [{"attr": "tensile", "op": "GT", "value": 500}])
    r = solve(s, "bridge")
    assert r.fitness is Tri.UNKNOWN                           # NOT a silent pass
    assert any("undeclared" in why for _, why in r.gaps)
    # PHYSICAL-class undeclared → existence UNKNOWN (could Rome? -> "unresolved", not "yes")
    s.assert_field("e_s", "constraints",
                   [{"attr": "tensile", "op": "GT", "value": 500, "class": "PHYSICAL"}])
    r = solve(s, "bridge")
    assert r.existence is Tri.UNKNOWN


# ------------------------------------------------------------------- TB-021 --

def test_tb021_platinum_or_palladium_and_heat():
    s = Store()
    s.create_node("pd"); s.create_node("heat"); s.create_node("widget")
    # platinum never created → stub → UNKNOWN branch
    s.create_edge("e_pt", "platinum", "widget", "IS_INGREDIENT_OF")
    s.create_edge("e_pd", "pd", "widget", "IS_INGREDIENT_OF")
    s.create_edge("e_h", "heat", "widget", "ENABLES")
    s.assert_field("widget", "requirement_expr",
                   ("or", ("edge", "e_pt"), ("and", ("edge", "e_pd"), ("edge", "e_h"))))
    r = solve(s, "widget")
    assert r.existence is Tri.SAT                             # pd+heat path proves it


# ------------------------------------------------------------- TB-002 / B1 ---

def test_tb002_bootstrap_loop_is_legal():
    s = Store()
    s.create_node("iron"); s.create_node("steel"); s.create_node("bessemer")
    s.create_edge("e1", "iron", "steel", "IS_INGREDIENT_OF")
    s.create_edge("e2", "steel", "bessemer", "IS_COMPONENT_OF")
    s.create_edge("e3", "bessemer", "steel", "OPTIMIZES")     # the loop-closer
    assert find_hard_cycles(View(s)) == []                    # OPTIMIZES exempt (ADR-0006)
    assert solve(s, "steel").existence is Tri.SAT             # terminates, no recursion trap
    assert solve(s, "bessemer").existence is Tri.SAT


def test_b1_hard_cycle_detected():
    s = Store()
    s.create_node("a"); s.create_node("b")
    s.create_edge("x", "a", "b", "IS_COMPONENT_OF")
    s.create_edge("y", "b", "a", "IS_COMPONENT_OF")
    assert find_hard_cycles(View(s))                          # flagged for review


# --------------------------------------------------- TB-057 (H11, ADR-0019) --

def test_tb057_excluded_leaf_is_vacuous():
    s = Store()
    s.create_node("iphone")                                   # family
    s.create_node("iphone1")
    s.create_edge("t1", "iphone1", "iphone", "IS_TYPE_OF")
    # family requires a front camera that is only a stub → family UNKNOWN
    s.create_edge("e_cam", "front_camera", "iphone", "IS_COMPONENT_OF")
    assert solve(s, "iphone").existence is Tri.UNKNOWN
    # the instance EXCLUDEs the inherited edge → vacuous, not VIOL, not UNKNOWN
    s.assert_field("iphone1", "excludes", ["e_cam"])
    assert solve(s, "iphone1").existence is Tri.SAT


# --------------------------------------------------------- TB-058 (H12) ------

def test_tb058_shadowed_exempt_and_satisfied_via_covering():
    s = Store()
    for n in ("copper", "wire", "motor"):
        s.create_node(n)
    s.create_edge("e500", "copper", "motor", "IS_INGREDIENT_OF")
    s.create_edge("e510", "copper", "wire", "IS_INGREDIENT_OF")
    s.create_edge("e511", "wire", "motor", "IS_COMPONENT_OF")
    s.assert_field("e500", "shadowed_by", ["e510", "e511"])
    # implicit-AND must skip e500 (shadowed) and use e511 → SAT
    assert solve(s, "motor").existence is Tri.SAT
    # authored expr referencing the SHADOWED edge is satisfied via covering (H12)
    s.assert_field("motor", "requirement_expr", ("edge", "e500"))
    assert solve(s, "motor").existence is Tri.SAT


# --------------------------------------------------------- TB-067 ------------

def test_tb067_constraints_ride_the_claim_through_shadow():
    s = Store()
    for n in ("copper", "wire", "motor"):
        s.create_node(n)
    s.create_edge("e500", "copper", "motor", "IS_INGREDIENT_OF")
    s.assert_field("e500", "constraints",
                   [{"attr": "conductivity", "op": "GT", "value": 50}])
    s.assert_field("copper", "attrs.conductivity", 59)
    s.create_edge("e510", "copper", "wire", "IS_INGREDIENT_OF")
    s.create_edge("e511", "wire", "motor", "IS_COMPONENT_OF")
    s.assert_field("e500", "shadowed_by", ["e510", "e511"])
    s.assert_field("motor", "requirement_expr", ("edge", "e500"))
    assert solve(s, "motor").fitness is Tri.SAT
    s.assert_field("copper", "attrs.conductivity", 10)        # demand still enforced
    assert solve(s, "motor").fitness is Tri.VIOL


# --------------------------------------------------------- TB-059 (H13) ------

def test_tb059_duplicate_twin_does_not_break_the_or():
    s = Store()
    s.create_node("pd"); s.create_node("widget")
    s.create_edge("e_pt", "platinum", "widget", "IS_INGREDIENT_OF")   # stub provider
    s.create_edge("e_pd", "pd", "widget", "IS_INGREDIENT_OF")
    s.assert_field("widget", "requirement_expr",
                   ("or", ("edge", "e_pt"), ("edge", "e_pd")))
    # a duplicate assertion of the SAME claim with a different UUID sneaks in:
    s.create_edge("e_pt_twin", "platinum", "widget", "IS_INGREDIENT_OF")
    r = solve(s, "widget")
    assert r.existence is Tri.SAT      # twin must NOT re-demand platinum via implicit-AND


# --------------------------------------------------------- TB-041 ------------

def test_tb041_hypothetical_guard_and_unlock_cascade():
    s = Store()
    s.create_node("rt_supercon", validity="hypothetical")     # 0 parents, pre-built future
    s.create_node("maglev_everywhere")
    s.create_edge("e_sc", "rt_supercon", "maglev_everywhere", "ENABLES")
    assert solve(s, "rt_supercon").existence is Tri.UNKNOWN   # no false magic-box unlock
    assert solve(s, "maglev_everywhere").existence is Tri.UNKNOWN
    t_before = len(s.facts)
    s.assert_field("rt_supercon", "validity", "current_truth")  # the physics lands
    assert solve(s, "maglev_everywhere").existence is Tri.SAT   # one flip cascades
    # ADR-0034: as-of the earlier record time, still UNKNOWN — history is honest
    assert realizable(View(s, at=t_before), "maglev_everywhere").existence is Tri.UNKNOWN


# --------------------------------------------------------- TB-042 ------------

def test_tb042_contradiction_is_a_missing_node_detector():
    s = Store()
    s.create_node("phlogiston", validity="disproven")
    s.create_node("theorem")                                   # proven true — a cited fact
    s.create_edge("e_p", "phlogiston", "theorem", "ENABLES")   # only recorded support
    out = contradictions(View(s))
    assert any(n == "theorem" for n, _ in out)                 # bounty, not paradox


# ---------------------------------------------------- TB-050 / H4 / H5 -------

def test_tb050_mobius_merge_rejected_and_unmerge_reopens():
    s = Store()
    s.create_node("a"); s.create_node("b")
    s.merge("a", "b")
    with pytest.raises(BreakerViolation):
        s.merge("b", "a")                                      # would close the loop
    s.unmerge("a")                                             # forward edit (H5)
    s.merge("b", "a")                                          # now legal
    assert View(s).resolve_redirect("b") == "a"


# --------------------------------------------------------- TB-068 ------------

def test_tb068_wire_or_with_unknown_silver():
    s = Store()
    for n in ("copper", "wire", "motor"):
        s.create_node(n)
    s.create_edge("e_cu", "copper", "wire", "IS_INGREDIENT_OF")
    s.create_edge("e_ag", "silver", "wire", "IS_INGREDIENT_OF")   # silver is a stub
    s.assert_field("wire", "requirement_expr", ("or", ("edge", "e_cu"), ("edge", "e_ag")))
    s.create_edge("e_w", "wire", "motor", "IS_COMPONENT_OF")
    r = solve(s, "motor")
    assert r.existence is Tri.SAT      # copper branch proves it; silver can't hurt
    # every consumer of wire inherits the alternative from ONE seam:
    s.create_node("telegraph")
    s.create_edge("e_w2", "wire", "telegraph", "IS_COMPONENT_OF")
    assert solve(s, "telegraph").existence is Tri.SAT


# ------------------------------------------------------------- H2 dates ------

def test_h2_temporal_certain_violation_only():
    # edge active from -150 ± 100 → interval [-250, -50]
    start = {"year": -150, "unc": 100}
    assert point_in_span(-300, Interval(**start), None) is Tri.VIOL     # certainly before
    assert point_in_span(-100, Interval(**start), None) is Tri.UNKNOWN  # overlap: honest
    assert point_in_span(0, Interval(**start), None) is Tri.SAT         # certainly after
    a, b = Interval(-150, 100), Interval(-100, 50)
    assert cmp_certain(a, b) is Tri.UNKNOWN                             # Antikythera case


def test_h2_temporal_gate_in_solve():
    s = Store()
    s.create_node("gears"); s.create_node("calculator")
    s.create_edge("e_g", "gears", "calculator", "IS_COMPONENT_OF")
    s.assert_field("e_g", "start_date", {"year": -150, "unc": 100})
    assert solve(s, "calculator", world_time=-300).existence is Tri.VIOL
    assert solve(s, "calculator", world_time=-100).existence is Tri.UNKNOWN
    assert solve(s, "calculator", world_time=0).existence is Tri.SAT


# ------------------------------------------------------------- H3 regions ----

def test_h3_regional_existential_composition():
    s = Store()
    s.create_node("concrete")
    s.assert_field("concrete", "timeline.geo:europe", [
        {"status": "ACTIVE", "start": -200, "end": 476},
        {"status": "LOST", "start": 476, "end": 1414},
        {"status": "ACTIVE", "start": 1414},
    ])
    v = View(s)
    assert available(v, "concrete", "geo:europe", 1000)[0] is Tri.VIOL   # lost
    assert available(v, "concrete", "geo:europe", 1500)[0] is Tri.SAT    # rediscovered
    assert available(v, "concrete", "geo:china", 1000)[0] is Tri.UNKNOWN # no data ≠ no
    s.assert_field("concrete", "timeline.geo:italy", [
        {"status": "ACTIVE", "start": 0, "end": 500},
        {"status": "LOST", "start": 300, "end": 800},
    ])
    tri, flags = available(View(s), "concrete", "geo:italy", 400)
    assert tri is Tri.SAT and flags                                       # overlap → bounty


# ---------------------------------------------------- ADR-0023 / TB-037 ------

def test_tb037_insertion_order_independence():
    def build(order):
        s = Store()
        ops = {
            "n1": lambda: s.create_node("iron"),
            "n2": lambda: s.create_node("steel"),
            "e": lambda: s.create_edge("e1", "iron", "steel", "IS_INGREDIENT_OF"),
        }
        for k in order:
            ops[k]()
        return s
    a = build(["n1", "n2", "e"])
    b = build(["e", "n2", "n1"])                 # edge added before either node exists
    assert solve(a, "steel").pair() == solve(b, "steel").pair()
    v_a, v_b = View(a), View(b)
    assert v_a.field("steel", "validity") == v_b.field("steel", "validity")


# ---------------------------------------------------- ADR-0034 as-of ---------

def test_adr034_asof_views_are_honest_history():
    s = Store()
    s.create_node("x", validity="hypothetical")
    t1 = len(s.facts)
    s.assert_field("x", "validity", "current_truth")
    assert realizable(View(s, at=t1), "x").existence is Tri.UNKNOWN
    assert realizable(View(s), "x").existence is Tri.SAT
    # both facts remain in the log forever (ADR-0011)
    assert "hypothetical" in s.dump() and "current_truth" in s.dump()


# ---------------------------------------------------- ADR-0038 identity ------

def test_adr038_identity_endures_corrections():
    s = Store()
    s.create_node("copper"); s.create_node("motor")
    s.create_edge("e_x", "copper", "motor", "IS_INGREDIENT_OF")
    s.assert_field("motor", "requirement_expr", ("edge", "e_x"))
    before = solve(s, "motor").pair()
    a1 = View(s).field_assertion("e_x", "start_date")
    s.assert_field("e_x", "start_date", {"year": 1830, "unc": 1})   # metadata correction
    s.assert_field("e_x", "start_date", {"year": 1832, "unc": 1})   # corrected again
    assert solve(s, "motor").pair() == before        # expression never dangled
    a2 = View(s).field_assertion("e_x", "start_date")
    assert a1 != a2                                   # evidence targets moved (assertions)
    assert View(s).edge("e_x")["from"] == "copper"    # identity endured (semantics)


# ---------------------------------------------------- ADR-0025 masks ---------

def test_adr025_possibility_never_gated_by_works_or_people():
    s = Store()
    s.create_node("newton", category="BIOLOGICAL_ENTITY")
    s.create_node("principia", category="WORK_PUBLICATION")
    s.create_node("calculus", category="FORMAL_CONCEPT")
    s.create_edge("e_n", "newton", "calculus", "ENABLES")      # contingent history
    s.create_edge("e_w", "principia", "calculus", "ENABLES")   # the 1800-paper trap
    r = solve(s, "calculus")
    assert r.existence is Tri.SAT                              # physics, not authorship


# ---------------------------------------------------- JSONL round-trip -------

def test_fact_log_roundtrip():
    s = _gate_world(Store())
    s2 = Store.load(s.dump())
    assert solve(s, "transistor").pair() == solve(s2, "transistor").pair()
    assert s.dump() == s2.dump()


# ---------------------------------------------------- redirects in solve -----

def test_merge_redirect_resolves_in_solve():
    s = Store()
    s.create_node("gasoline"); s.create_node("petrol"); s.create_node("car")
    s.create_edge("e_f", "petrol", "car", "IS_INGREDIENT_OF")
    s.merge("petrol", "gasoline")                              # duplicate healed
    assert solve(s, "car").existence is Tri.SAT                # resolves via redirect
