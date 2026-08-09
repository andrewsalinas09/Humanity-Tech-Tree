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
    pg.migrate(os.path.join(MIG, "003_requests.sql"))
    pg.migrate(os.path.join(MIG, "004_users.sql"))
    pg.migrate(os.path.join(MIG, "005_admin_model.sql"))
    pg.migrate(os.path.join(MIG, "006_embeddings.sql"))
    pg.migrate(os.path.join(MIG, "007_reputation_numeric.sql"))
    pg.migrate(os.path.join(MIG, "008_max_reputation.sql"))
    pg.migrate(os.path.join(MIG, "009_linter_user.sql"))
    pg.migrate(os.path.join(MIG, "010_want_description.sql"))
    pg.wipe()
    with pg.conn.cursor() as c:
        c.execute("TRUNCATE credentials, users, requests, request_endorsements, "
                  "decision_tickets, search_receipts RESTART IDENTITY CASCADE")
    pg.conn.commit()
    s = Service(pg)
    s.create_identity("tok-andrew", {"type": "human", "id": "andrew"})
    s.create_identity("tok-agent", {"type": "agent", "id": "seed-1",
                                    "operator": "andrew",
                                    "model": "claude-fable-5"}, budget_per_hour=1000)
    with pg.conn.cursor() as c:      # 005 grants andrew admin; truncation undid it
        c.execute("UPDATE users SET is_admin=TRUE WHERE user_id='andrew'")
    pg.conn.commit()
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
    svc.create_identity("tok-tiny", {"type": "agent", "id": "tiny",
                                     "operator": "andrew"}, budget_per_hour=2)
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


def test_delete_ticket_is_admin_gated(svc):
    r = svc.search_similar("tok-agent", "oops")
    svc.propose_node("tok-agent", "Oops Node", search_receipt=r["receipt"],
                     node_id="oops-node")
    t = svc.request_deletion("tok-agent", "oops-node", "created in error")
    assert t["ticket"]
    # the requesting agent cannot approve its own deletion
    out = svc.resolve_decision("tok-agent", t["ticket"], {"key": "approve"})
    assert out["rejected"]["rule"] == "ADMIN"
    # the admin can; the node vanishes from the view but the log keeps it
    out = svc.resolve_decision("tok-andrew", t["ticket"], {"key": "approve"})
    assert "applied" in out
    _, view = svc._kernel()
    assert view.node("oops-node") is None
    assert "oops-node" in view.tombstoned


def test_edge_tombstone_admin_gated_history_preserved(svc):
    svc.pg.quick(lambda cr: (cr.create_node("em"), cr.create_node("tr")))
    svc.pg.quick(lambda cr: cr.create_edge("e_em_tr", "em", "tr", "ENABLES"))
    t = svc.request_deletion("tok-agent", "e_em_tr",
                             "correct but superseded by the finer chain")
    assert svc.resolve_decision("tok-agent", t["ticket"],
                                {"key": "approve"})["rejected"]["rule"] == "ADMIN"
    out = svc.resolve_decision("tok-andrew", t["ticket"], {"key": "approve"})
    assert "applied" in out
    store, view = svc._kernel()
    assert view.edge("e_em_tr") is None                  # gone from the view
    assert view.node("em") and view.node("tr")           # endpoints untouched
    from httk import View
    seq_before = next(f["recorded_at"] for f in store.facts
                      if f["kind"] == "edge.create"
                      and f["body"]["edge_id"] == "e_em_tr")
    past = View(store, at=seq_before)
    assert past.edge("e_em_tr") is not None              # HISTORY PRESERVED


def test_reputation_and_challenge_loop(svc):
    """ADR-0049 end to end: verify -> earn; challenge -> vote -> admin ratify
    -> remedy executes -> demotion slashes gently (-1, never clawback)."""
    r = svc.search_similar("tok-agent", "gizmo")
    out = svc.propose_node("tok-agent", "Gizmo", search_receipt=r["receipt"],
                           node_id="gizmo", description="A test gizmo.")
    aid = out["applied"]["created"]["assertions"][0]["assertion_id"]  # name
    # machine verification earns the author L3 rep (+1) and the verifier +1
    v = svc.verify_citation("tok-agent", aid, "supported", model="test-model")
    assert "applied" in v
    with svc.pg.conn.cursor() as c:
        c.execute("SELECT reputation FROM users WHERE user_id='seed-1'")
        assert c.fetchone()[0] == 2                    # author +1, verifier +1
    # challenge the claim with a pre-staged remedy
    ch = svc.open_challenge("tok-andrew", "gizmo",
                            "test: gizmo is misnamed",
                            remedy=[{"verb": "add_alias",
                                     "params": {"node_id": "gizmo",
                                                "alias": "Widget-X"}}])
    cid = ch["challenge"]
    assert svc.vote_challenge("tok-agent", cid, True, "agree, evidence says so")
    t = svc.challenge_tally("tok-andrew", cid)
    assert t["votes"][0]["vested"] is False            # <3 verified claims
    # non-admin cannot ratify
    bad = svc.resolve_challenge("tok-agent", cid, "upheld")
    assert bad["rejected"]["rule"] == "ADMIN"
    done = svc.resolve_challenge("tok-andrew", cid, "upheld", demoted=[aid])
    assert done["remedy_results"][0]["result"].get("applied")
    _, view = svc._kernel()
    assert "Widget-X" in (view.field("gizmo", "aliases") or [])
    with svc.pg.conn.cursor() as c:
        # author: +1 (L3) -1 (demoted) = 0; verifier stance now bad-vouch -2
        # seed-1 was both author and verifier: 1 - 1 - 2 = -2
        c.execute("SELECT reputation FROM users WHERE user_id='seed-1'")
        assert c.fetchone()[0] == -2
        # andrew: +3 for the upheld challenge (opened_by), minus agent rollup -1.5
        c.execute("SELECT reputation FROM users WHERE user_id='andrew'")
        assert float(c.fetchone()[0]) == 1.5


def test_galaxy_scenario_extract_family(svc):
    """The late-arriving taxonomy parent, end to end: siblings wired flat ->
    linter files a bounty -> extract_family ticket (grouped hoist choice) ->
    family edges + shadowed instance edges (history preserved)."""
    def seed(cr):
        for n in ("cpu2", "battery2", "wifi2", "glass2", "iphone2", "galaxy2"):
            cr.create_node(n)
    svc.pg.quick(seed)
    def wire(cr):
        for s in ("iphone2", "galaxy2"):
            for p in ("cpu2", "battery2", "wifi2", "glass2"):
                cr.create_edge(f"e_{p}_{s}", p, s, "IS_COMPONENT_OF")
    svc.pg.quick(wire)
    # the linter notices the sibling cluster and files a bounty
    out = svc.run_sibling_linter(min_shared=4)
    assert any("galaxy2 + iphone2" in w for w in out["posted"])
    assert not svc.run_sibling_linter(min_shared=4)["posted"]   # deduped
    # the heal: create the parent, extract the family
    r = svc.search_similar("tok-andrew", "smartphone2")
    svc.propose_node("tok-andrew", "Smartphone2", search_receipt=r["receipt"],
                     node_id="smartphone2")
    out = svc.execute("tok-andrew", "extract_family",
                      {"parent": "smartphone2",
                       "siblings": ["iphone2", "galaxy2"]})
    assert "ticket" in out                       # refuses to guess the hoist
    assert len(out["evidence"]["shared"]) == 4   # grouped evidence rides along
    done = svc.resolve_decision("tok-andrew", out["ticket"],
                                {"key": "hoist_except", "exclude": ["glass2"]},
                                justification="glass differs per maker")
    assert "applied" in done
    _, view = svc._kernel()
    # family edges exist; instance edges shadowed (except glass, which stays)
    assert view.edge("e_cpu2_smartphone2")
    assert view.is_shadowed("e_cpu2_iphone2") and view.is_shadowed("e_cpu2_galaxy2")
    assert not view.is_shadowed("e_glass2_iphone2")
    assert any(e["to"] == "smartphone2"
               for e in view.edges_out("iphone2", {"IS_TYPE_OF"}))
    # no re-fire: siblings now share a parent
    assert not svc.run_sibling_linter(min_shared=4)["posted"]
