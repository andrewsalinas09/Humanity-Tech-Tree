"""Backend acceptance: the DB is an index over the fact log, and the kernel is the
semantics. The killer test: author through Postgres, export the JSONL fact log,
load it into the KERNEL, solve — identical to authoring in the kernel directly.
One semantics, two substrates.
"""
import os

import pytest

from httkdb.factlog import PgFactLog, BreakerViolation
from httk import Store, View, realizable, Tri

MIGRATION = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "migrations", "001_init.sql")


@pytest.fixture()
def pg():
    try:
        log = PgFactLog()
    except Exception as e:                                    # pragma: no cover
        pytest.skip(f"no postgres reachable: {e}")
    log.migrate(MIGRATION)
    log.wipe()
    yield log
    log.close()


def db_solve(pg_log, node, **kw):
    """Export the DB's fact log and solve with the KERNEL — the semantics bridge."""
    return realizable(View(Store.load(pg_log.export_jsonl())), node, **kw)


def _author_gate_world(cr):
    cr.create_node("silicon"); cr.assert_field("silicon", "attrs.purity", 0.999999)
    cr.create_node("transistor")
    cr.create_edge("e_si", "silicon", "transistor", "IS_INGREDIENT_OF")
    cr.assert_field("e_si", "constraints",
                    [{"attr": "purity", "op": "GT", "value": 0.99999, "class": "PHYSICAL"}])
    cr.create_node("tube"); cr.assert_field("tube", "attrs.power_per_gate", 2.0)
    cr.assert_field("transistor", "attrs.power_per_gate", 1e-7)
    cr.create_node("gate")
    cr.create_edge("e_t", "transistor", "gate", "IS_COMPONENT_OF")
    cr.create_edge("e_v", "tube", "gate", "IS_COMPONENT_OF")
    per_gate = [{"attr": "power_per_gate", "op": "LT", "value": 0.001}]
    cr.assert_field("e_t", "constraints", per_gate)
    cr.assert_field("e_v", "constraints", per_gate)
    cr.assert_field("gate", "requirement_expr", ["or", ["edge", "e_t"], ["edge", "e_v"]])


def test_db_export_solves_identically_to_kernel(pg):
    status, flags, _ = pg.quick(_author_gate_world)
    assert status == "merged" and not flags
    r = db_solve(pg, "gate")
    assert r.existence is Tri.SAT and r.fitness is Tri.SAT    # transistor branch wins
    assert db_solve(pg, "transistor").existence is Tri.SAT


def test_cr_apply_is_commutative(pg):
    def cr_nodes(cr):
        cr.create_node("iron"); cr.create_node("steel")

    def cr_edge(cr):
        cr.create_edge("e1", "iron", "steel", "IS_INGREDIENT_OF")

    pg.quick(cr_edge)                                          # edge BEFORE nodes exist
    pg.quick(cr_nodes)
    a = db_solve(pg, "steel").pair()
    pg.wipe()
    pg.quick(cr_nodes)                                         # opposite order
    pg.quick(cr_edge)
    b = db_solve(pg, "steel").pair()
    assert a == b == (Tri.SAT, Tri.SAT)                        # ADR-0023 in the database


def test_b4_redirect_cycle_hard_rejects(pg):
    pg.quick(lambda cr: (cr.create_node("a"), cr.create_node("b")))
    pg.quick(lambda cr: cr.assert_field("a", "migrated_to", "b"))
    with pg.conn.cursor() as c:
        c.execute("SELECT COUNT(*) FROM facts"); before = c.fetchone()[0]
    cr = pg.open_cr()
    cr.assert_field("b", "migrated_to", "a")                   # the Möbius merge
    with pytest.raises(BreakerViolation):
        pg.apply(cr)
    with pg.conn.cursor() as c:
        c.execute("SELECT COUNT(*) FROM facts"); after = c.fetchone()[0]
        c.execute("SELECT status FROM change_requests WHERE cr_id=%s", (cr.cr_id,))
        assert c.fetchone()[0] == "flagged"
    assert before == after                                     # nothing written (H4 hard)


def test_h9_jointly_cyclic_crs_merge_but_flag(pg):
    pg.quick(lambda cr: (cr.create_node("a"), cr.create_node("b")))
    s1, f1, _ = pg.quick(lambda cr: cr.create_edge("x", "a", "b", "IS_COMPONENT_OF"))
    assert s1 == "merged" and not f1                           # individually innocent
    s2, f2, _ = pg.quick(lambda cr: cr.create_edge("y", "b", "a", "IS_COMPONENT_OF"))
    assert s2 == "flagged" and any("cycle" in f for f in f2)   # flags, never reorders (H9)


def test_retraction_recomputes_to_previous(pg):
    pg.quick(lambda cr: cr.create_node("x", validity="hypothetical"))
    pg.quick(lambda cr: cr.assert_field("x", "validity", "current_truth"))
    with pg.conn.cursor() as c:
        c.execute("SELECT assertion_fact_id FROM current_fields "
                  "WHERE subject_id='x' AND field_path='validity'")
        current = c.fetchone()[0]
    pg.quick(lambda cr: cr.retract(current))                   # forward fact (ADR-0011)
    with pg.conn.cursor() as c:
        c.execute("SELECT value FROM current_fields "
                  "WHERE subject_id='x' AND field_path='validity'")
        assert c.fetchone()[0] == "hypothetical"               # reverted to prior claim
    assert db_solve(pg, "x").existence is Tri.UNKNOWN          # kernel agrees


def test_rebuild_projections_equals_incremental(pg):
    pg.quick(_author_gate_world)
    with pg.conn.cursor() as c:
        c.execute("SELECT * FROM current_fields ORDER BY subject_id, field_path")
        before = c.fetchall()
    pg.rebuild_projections()
    with pg.conn.cursor() as c:
        c.execute("SELECT * FROM current_fields ORDER BY subject_id, field_path")
        after = c.fetchall()
    assert before == after                                     # pure index over the log


def test_citation_carries_locator(pg):
    pg.quick(lambda cr: cr.create_node("iron"))
    pg.quick(lambda cr: cr.assert_field("iron", "attrs.melting_point", 1811))
    with pg.conn.cursor() as c:
        c.execute("SELECT assertion_fact_id FROM current_fields "
                  "WHERE subject_id='iron' AND field_path='attrs.melting_point'")
        claim = c.fetchone()[0]
    pg.quick(lambda cr: (cr.create_node("handbook", category="WORK_PUBLICATION"),
                         cr.cite(claim, "handbook", locator="p. 412, table 3")))
    with pg.conn.cursor() as c:
        c.execute("SELECT source_node, locator FROM citations "
                  "WHERE claim_assertion_id=%s", (claim,))
        assert c.fetchone() == ("handbook", "p. 412, table 3")
