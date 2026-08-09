"""Service acceptance: identity stamping, budgets, the unskippable gate, tickets."""
import os

import pytest

from httkdb.factlog import PgFactLog
from httkserver.service import Service, AuthError, BudgetExceeded

MIG = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                   "backend", "migrations")


@pytest.fixture()
def svc():
    try:
        pg = PgFactLog()
    except Exception as e:                                     # pragma: no cover
        pytest.skip(f"no postgres: {e}")
    pg.migrate(os.path.join(MIG, "001_init.sql"))
    pg.migrate(os.path.join(MIG, "002_server.sql"))
    pg.wipe()
    with pg.conn.cursor() as c:
        c.execute("TRUNCATE identities, decision_tickets, search_receipts "
                  "RESTART IDENTITY CASCADE")
    pg.conn.commit()
    s = Service(pg)
    s.create_identity("tok-andrew", {"type": "human", "id": "andrew"})
    s.create_identity("tok-agent", {"type": "agent", "id": "seed-1",
                                    "model": "claude-fable-5"}, budget_per_hour=1000)
    yield s
    pg.close()


def test_unknown_credential_rejected(svc):
    with pytest.raises(AuthError):
        svc.search_similar("tok-nope", "iron")


def test_identity_is_stamped_server_side(svc):
    r = svc.search_similar("tok-agent", "iron")
    out = svc.propose_node("tok-agent", "Iron", category="MATERIAL",
                           search_receipt=r["receipt"])
    assert "applied" in out
    with svc.pg.conn.cursor() as c:
        c.execute("SELECT DISTINCT author->>'id', author->>'model' FROM facts")
        rows = c.fetchall()
    assert rows == [("seed-1", "claude-fable-5")]              # the server said who


def test_budget_enforced(svc):
    svc.create_identity("tok-tiny", {"type": "agent", "id": "tiny"}, budget_per_hour=2)
    r = svc.search_similar("tok-tiny", "aaa")
    svc.propose_node("tok-tiny", "Aaa", search_receipt=r["receipt"])   # writes 2 facts
    with pytest.raises(BudgetExceeded):
        r2 = svc.search_similar("tok-tiny", "bbb")
        svc.propose_node("tok-tiny", "Bbb", search_receipt=r2["receipt"])


def test_blame_corollary_no_default_vouching(svc):
    """Unstated validity stays ABSENT: the node stands at UNKNOWN until someone
    personally vouches — no parameter default ever vouches for the caller."""
    r = svc.search_similar("tok-agent", "widget")
    svc.propose_node("tok-agent", "Widget", search_receipt=r["receipt"])
    assert svc.solve("tok-agent", "widget")["existence"] == "UNKNOWN"
    out = svc.execute("tok-andrew", "correct",
                      {"subject": "widget", "fld": "validity",
                       "new_value": "current_truth",
                       "justification": "verified it exists"})
    assert "applied" in out
    assert svc.solve("tok-andrew", "widget")["existence"] == "SATISFIED"
    with svc.pg.conn.cursor() as c:                            # blame is assigned
        c.execute("SELECT author->>'id' FROM facts WHERE "
                  "body->>'field'='validity' AND body->>'subject'='widget'")
        assert c.fetchone()[0] == "andrew"                     # a PERSON vouched


def test_the_gate_is_unskippable(svc):
    out = svc.propose_node("tok-andrew", "Steel")              # no receipt
    assert out["rejected"]["rule"] == "Q-20"


def test_duplicate_opens_ticket_and_resolves_create_anyway(svc):
    r = svc.search_similar("tok-andrew", "gasoline")
    svc.propose_node("tok-andrew", "Gasoline", category="MATERIAL",
                     search_receipt=r["receipt"])
    r2 = svc.search_similar("tok-andrew", "gasoline")
    out = svc.propose_node("tok-andrew", "Gasoline", category="MATERIAL",
                           search_receipt=r2["receipt"])
    assert "ticket" in out                                     # refused to guess
    keys = {o["key"] for o in out["options"]}
    assert keys == {"use_existing", "create_anyway"}
    done = svc.resolve_decision("tok-andrew", out["ticket"],
                                {"key": "use_existing", "node_id": "gasoline"})
    assert done["applied"]["existing"] == "gasoline"
    with svc.pg.conn.cursor() as c:
        c.execute("SELECT status, resolved_by->>'id' FROM decision_tickets")
        assert c.fetchone() == ("resolved", "andrew")          # provenanced pick


def test_l11_ticket_roundtrip_compiles_the_or(svc):
    def seed(cr):
        for n in ("metal", "copper", "silver", "wire"):
            cr.create_node(n)
        cr.create_edge("t1", "copper", "metal", "IS_TYPE_OF")
        cr.create_edge("t2", "silver", "metal", "IS_TYPE_OF")
    svc.pg.quick(seed)
    out = svc.execute("tok-agent", "add_ingredient",
                      {"product": "wire", "ingredient": "copper", "edge_id": "e_cu"})
    assert "applied" in out
    out = svc.execute("tok-agent", "add_ingredient",
                      {"product": "wire", "ingredient": "silver", "edge_id": "e_ag"})
    assert "ticket" in out                                     # L11: same-role fork
    bad = svc.resolve_decision("tok-andrew", out["ticket"],
                               {"key": "alternative", "to": "e_zz"})
    assert "rejected" in bad                                   # outside the legal set
    done = svc.resolve_decision("tok-andrew", out["ticket"],
                                {"key": "alternative", "to": "e_cu"})
    assert "applied" in done
    solved = svc.solve("tok-andrew", "wire")
    assert solved["existence"] == "SATISFIED"                  # the OR, end to end


def test_rejections_pass_through(svc):
    svc.pg.quick(lambda cr: (cr.create_node("factory"),
                             cr.create_node("worker", category="BIOLOGICAL_ENTITY")))
    out = svc.execute("tok-andrew", "add_component",
                      {"whole": "factory", "part": "worker"})
    assert out["rejected"]["rule"] == "L5"


def test_open_tickets_lists_the_queue(svc):
    svc.pg.quick(lambda cr: (cr.create_node("m"), cr.create_node("cu"),
                             cr.create_node("ag"), cr.create_node("w")))
    svc.pg.quick(lambda cr: (cr.create_edge("t1", "cu", "m", "IS_TYPE_OF"),
                             cr.create_edge("t2", "ag", "m", "IS_TYPE_OF")))
    svc.execute("tok-agent", "add_ingredient",
                {"product": "w", "ingredient": "cu", "edge_id": "e1"})
    svc.execute("tok-agent", "add_ingredient", {"product": "w", "ingredient": "ag"})
    q = svc.open_tickets("tok-andrew")
    assert len(q) == 1 and q[0]["verb"] == "add_ingredient"    # the check queue exists
