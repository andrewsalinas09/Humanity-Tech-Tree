"""The transport-agnostic verb service (ADR-0041).

execute(token, verb, params) →
  {"applied": ...}   StagedFacts compiled, applied as a CR authored by the token's
                     identity (server-stamped — callers are never trusted)
  {"ticket": ...}    the verb refused to guess; Decision persisted as a ticket
  {"rejected": ...}  typed rule verdict
resolve(token, ticket_id, choice) merges the choice into the stored params and
re-executes — the pick lands as provenanced content (ADR-0040/0041).
"""
import hashlib
import json

from psycopg.types.json import Jsonb

from httk import Store, View, realizable
from httk import verbs as VB
from httk.verbs import StagedFacts, Decision, Rejection

from httkserver import embeds, reputation


class AuthError(Exception):
    pass


class BudgetExceeded(Exception):
    pass


# verb registry: name -> (fn, needs_store)
VERBS = {
    "add_component": (VB.add_component, False),
    "add_ingredient": (VB.add_ingredient, False),
    "add_enabler": (VB.add_enabler, False),
    "classify": (VB.classify, False),
    "refine": (VB.refine, False),
    "succeed": (VB.succeed, False),
    "associate": (VB.associate, False),
    "intercept": (VB.intercept, False),
    "exclude": (VB.exclude, False),
    "widen": (VB.widen, False),
    "merge": (VB.merge, False),
    "set_constraint": (VB.set_constraint, False),
    "set_attribute": (VB.set_attribute, False),
    "add_time_segment": (VB.add_time_segment, False),
    "date_edge": (VB.date_edge, False),
    "add_iteration": (VB.add_iteration, False),
    "lift_iteration": (VB.lift_iteration, False),
    "rename": (VB.rename, False),
    "add_alias": (VB.add_alias, False),
    "reclassify": (VB.reclassify, False),
    "retract_assertion": (VB.retract_assertion, False),
    "mark_shadowed": (VB.mark_shadowed, False),
    "add_alternative_bundle": (VB.add_alternative_bundle, False),
    "extract_family": (VB.extract_family, False),
    "attach_citation": (VB.attach_citation, False),
    "correct": (VB.correct, False),
    "flag": (VB.flag, False),
    "move_assertion": (VB.move_assertion, True),
    "park_assertion": (VB.park_assertion, True),
    "unmerge": (VB.unmerge, True),
}

# how a ticket choice merges back into params, per verb (ADR-0041 §3)
def _merge_choice(verb, params, choice):
    p = dict(params)
    if verb in ("add_component", "add_ingredient"):
        if choice["key"] == "additional":
            p["role"] = "additional"
        else:
            p["role"] = {"alternative": choice["to"]}
    elif verb == "widen":
        p["to_ancestor"] = choice["key"]
    elif verb == "intercept":
        p["first_leg_type"] = choice["first"]
        p["second_leg_type"] = choice["second"]
    elif verb == "propose_node":
        p["duplicate_resolution"] = choice
    elif verb == "extract_family":
        p["hoist_choice"] = choice
    else:
        p["choice"] = choice
    return p


class Service:
    def __init__(self, pg):
        self.pg = pg

    # -- identity ------------------------------------------------------------
    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def create_identity(self, token, identity, budget_per_hour=1000):
        """User + first credential (user DB rulings 2026-08-09): identity ≠
        credential. Agents REQUIRE an operator — blame rolls up to people."""
        uid = identity.get("id")
        kind = identity.get("type", "human")
        operator = identity.get("operator")
        if kind == "agent" and not operator:
            raise AuthError(f"agent '{uid}' needs an operator (accountability "
                            "chain: no orphan agents)")
        with self.pg.conn.cursor() as c:
            c.execute(
                "INSERT INTO users (user_id, display_name, kind, operator, model) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO NOTHING",
                (uid, identity.get("display_name", uid), kind, operator,
                 identity.get("model")))
            c.execute(
                "INSERT INTO credentials (token_hash, user_id, budget_per_hour) "
                "VALUES (%s,%s,%s) ON CONFLICT (token_hash) DO UPDATE "
                "SET user_id=EXCLUDED.user_id, "
                "budget_per_hour=EXCLUDED.budget_per_hour, revoked_at=NULL",
                (self.hash_token(token), uid, budget_per_hour))
        self.pg.conn.commit()

    def revoke_credential(self, token):
        with self.pg.conn.cursor() as c:
            c.execute("UPDATE credentials SET revoked_at=now() "
                      "WHERE token_hash=%s", (self.hash_token(token),))

    def authenticate(self, token):
        with self.pg.conn.cursor() as c:
            c.execute(
                "SELECT u.user_id, u.kind, u.model, u.is_admin, "
                "c.budget_per_hour "
                "FROM credentials c JOIN users u ON u.user_id = c.user_id "
                "WHERE c.token_hash=%s AND c.revoked_at IS NULL",
                (self.hash_token(token),))
            row = c.fetchone()
        if not row:
            raise AuthError("unknown credential")
        ident = {"type": row[1], "id": row[0]}
        if row[2]:
            ident["model"] = row[2]
        if row[3]:
            ident["admin"] = True
        return ident, row[4]

    def _check_budget(self, identity, budget):
        with self.pg.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM facts WHERE author->>'id'=%s "
                      "AND wall_time > now() - interval '1 hour'",
                      (identity.get("id"),))
            used = c.fetchone()[0]
        if used >= budget:
            raise BudgetExceeded(f"{identity.get('id')}: {used}/{budget} facts this hour")

    # -- kernel view over the DB ---------------------------------------------
    def _kernel(self):
        store = Store.load(self.pg.export_jsonl())
        return store, View(store)

    # -- reads ---------------------------------------------------------------
    def search_similar(self, token, query):
        """The two-lane existence gate (ADR-0048): exact/substring matching
        (what forces duplicate tickets) + SEMANTIC candidates over the node
        embeddings, with descriptions and scores — the CALLER judges (no LLM
        in the transaction, ADR-0040; the callers are LLMs). The receipt
        records both lanes: 'you were shown X' is on the books."""
        identity, _ = self.authenticate(token)
        _, view = self._kernel()
        q = query.lower()
        hits = []
        for n in view.nodes():
            names = [n, view.field(n, "name") or ""] + (view.field(n, "aliases", []) or [])
            if any(q == str(x).lower() or q in str(x).lower() for x in names if x):
                hits.append({"node_id": n, "category": view.node(n)["category"]})
        try:
            embeds.refresh(self.pg, view)
            semantic = embeds.semantic_search(self.pg, view, query)
        except Exception as e:                     # gate degrades, never blocks
            semantic = []
            print(f"semantic lane unavailable: {e}")
        with self.pg.conn.cursor() as c:
            c.execute("INSERT INTO search_receipts (query, results, issued_to) "
                      "VALUES (%s,%s,%s) RETURNING receipt_id",
                      (query, Jsonb({"matches": hits, "semantic": semantic}),
                       Jsonb(identity)))
            rid = c.fetchone()[0]
        self.pg.conn.commit()
        return {"receipt": rid, "matches": hits, "semantic": semantic}

    def list_nodes(self, token, category=None, k=500):
        """Browse affordance (agent friction #1b): the graph is enumerable."""
        self.authenticate(token)
        _, view = self._kernel()
        out = []
        for n in sorted(view.nodes()):
            cat = (view.node(n) or {}).get("category")
            if category and cat != category:
                continue
            out.append({"node_id": n, "name": view.field(n, "name") or n,
                        "category": cat})
        return out[:k]

    def solve(self, token, node_id, world_time=None, region=None):
        self.authenticate(token)
        _, view = self._kernel()
        r = realizable(view, node_id, world_time=world_time, region=region)
        return {"existence": r.existence.value, "fitness": r.fitness.value,
                "gaps": r.gaps, "unfit": r.unfit}

    def get_node(self, token, node_id):
        self.authenticate(token)
        _, view = self._kernel()
        n = view.node(node_id)
        if n is None:
            return {"missing": node_id}
        return {"node": n,
                # assertion ids ride along — attach_citation targets ASSERTIONS
                # (ADR-0038); without these an MCP agent could never cite
                "fields": {k[1]: {"value": v[1], "assertion": v[0]}
                           for k, v in view._fields.items() if k[0] == node_id},
                "edges_in": view.edges_in(node_id),
                "edges_out": view.edges_out(node_id)}

    # -- writes ---------------------------------------------------------------
    def propose_node(self, token, name, category="TECHNOLOGY",
                     validity=None, search_receipt=None,
                     duplicate_resolution=None, node_id=None,
                     description=None):
        """The gate is unskippable by construction: a receipt for a matching query
        is REQUIRED; exact matches force a Decision (use-existing vs create-anyway)."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if search_receipt is None:
            return {"rejected": {"rule": "Q-20",
                                 "message": "search_similar first — the existence "
                                            "gate is not optional"}}
        with self.pg.conn.cursor() as c:
            c.execute("SELECT query, results FROM search_receipts WHERE receipt_id=%s",
                      (search_receipt,))
            row = c.fetchone()
        if not row:
            return {"rejected": {"rule": "Q-20", "message": "unknown receipt"}}
        _, results = row
        matches = results["matches"] if isinstance(results, dict) else results
        exact = [m for m in matches if m["node_id"].lower() == (node_id or name).lower()
                 or name.lower() in m["node_id"].lower()]
        if exact and duplicate_resolution is None:
            return self._open_ticket(
                identity, "propose_node",
                {"name": name, "category": category, "validity": validity,
                 "search_receipt": search_receipt, "node_id": node_id},
                "near-duplicates found: use existing or create anyway (TB-032: "
                "err toward creating; duplicates heal by merge)",
                [{"key": "use_existing", "node_id": m["node_id"]} for m in exact]
                + [{"key": "create_anyway", "justification_required": True}])
        if (duplicate_resolution or {}).get("key") == "use_existing":
            return {"applied": {"existing": duplicate_resolution["node_id"],
                                "facts_written": 0}}
        nid = node_id or name.lower().replace(" ", "-")
        facts = [("node.create", {"node_id": nid, "category": category}),
                 ("assert", {"subject": nid, "field": "name", "value": name})]
        if description:                            # encouraged, never required
            facts.append(("assert", {"subject": nid, "field": "description",
                                     "value": description}))
        if validity is not None:                   # blame corollary (ADR-0042):
            facts.append(("assert", {"subject": nid, "field": "validity",
                                     "value": validity}))
        # unstated validity stays ABSENT — the node stands at UNKNOWN until
        # someone personally vouches; no default ever vouches for the caller.
        return self._apply(identity, facts, notes=[])

    def execute(self, token, verb, params):
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if verb not in VERBS:
            return {"rejected": {"rule": "E404", "message": f"unknown verb {verb}"}}
        if verb == "attach_citation" and "subject" not in params:
            # always-connected rule: resolve the claim's subject so the verb can
            # lay the source's ASSOCIATION(documents) edge
            with self.pg.conn.cursor() as c:
                c.execute("SELECT body FROM facts WHERE fact_id=%s AND kind='assert'",
                          (params.get("assertion_id"),))
                row = c.fetchone()
            if row:
                params = {**params, "subject": row[0].get("subject")}
        fn, needs_store = VERBS[verb]
        store, view = self._kernel()
        result = fn(store, view, **params) if needs_store else fn(view, **params)
        if isinstance(result, Rejection):
            return {"rejected": {"rule": result.rule, "message": result.message}}
        if isinstance(result, Decision):
            return self._open_ticket(identity, verb, params, result.reason,
                                     result.options, result.evidence)
        if isinstance(result, tuple):                     # unmerge: (staged, triage)
            staged, triage = result
            out = self._apply(identity, staged.facts, staged.notes)
            out["triage_tickets"] = [
                self._open_ticket(identity, "triage_assertion",
                                  {"decision": d.reason}, d.reason, d.options)["ticket"]
                for d in triage]
            return out
        return self._apply(identity, result.facts, result.notes)

    def request_deletion(self, token, subject_id, reason):
        """ADR-0047 (Q-23): anyone may MARK a node or edge for deletion —
        created-in-error nodes, or correct-but-no-longer-useful edges (coarse
        history superseded by richer structure). Only an ADMIN approves.
        Approval writes a tombstone fact — the log keeps everything; as-of
        reads before the tombstone still see it (HISTORY PRESERVED)."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        _, view = self._kernel()
        if view.node(subject_id):
            kind = "node"
        elif view.edge(subject_id):
            kind = "edge"
        else:
            return {"rejected": {"rule": "E404", "message": f"{subject_id}?"}}
        if not reason:
            return {"rejected": {"rule": "ADR-0047",
                                 "message": "deletion requires a reason"}}
        return self._open_ticket(
            identity, "delete",
            {"subject": subject_id, "kind": kind, "reason": reason},
            f"ADMIN-ONLY: tombstone {kind} '{subject_id}' — {reason}",
            [{"key": "approve"}, {"key": "deny"}])

    def resolve_decision(self, token, ticket_id, choice, justification=None):
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT verb, params, status, options FROM decision_tickets "
                      "WHERE ticket_id=%s", (ticket_id,))
            row = c.fetchone()
        if not row:
            return {"rejected": {"rule": "E404", "message": f"ticket {ticket_id}?"}}
        verb, params, status, options = row
        if status != "open":
            return {"rejected": {"rule": "TICKET", "message": f"ticket is {status}"}}
        MARKERS = {"justification_required", "exclude", "include"}

        def _matches(opt):
            if opt.get("key") != choice.get("key"):
                return False
            return all(choice.get(k) == v for k, v in opt.items()
                       if k != "key" and k not in MARKERS)

        if not any(_matches(o) for o in options):
            return {"rejected": {"rule": "ADR-0040",
                                 "message": "choice outside the legal option set"}}
        merged = _merge_choice(verb, params, choice)
        if justification:
            merged.setdefault("justification", justification)
        if verb in ("delete", "delete_node"):
            # ADR-0047: the wrongness stakes of hiding truth (ADR-0015) put
            # tombstones behind the admin gate — requesting is open, approving
            # is not
            if not identity.get("admin"):
                return {"rejected": {"rule": "ADMIN",
                                     "message": "delete tickets can only be "
                                                "approved by an admin"}}
            if choice.get("key") == "approve":
                subj = params.get("subject") or params.get("node_id")
                kind = params.get("kind", "node")
                fact = (("edge.tombstone", {"edge_id": subj,
                                            "reason": params.get("reason", "")})
                        if kind == "edge" else
                        ("node.tombstone", {"node_id": subj,
                                            "reason": params.get("reason", "")}))
                out = self._apply(identity, [fact],
                                  [f"tombstone approved: {params.get('reason')}"])
            else:
                out = {"denied": ticket_id}
        elif verb == "propose_node":
            out = self.propose_node(token, **merged)
        else:
            out = self.execute(token, verb, merged)
        with self.pg.conn.cursor() as c:
            c.execute("UPDATE decision_tickets SET status='resolved', choice=%s, "
                      "resolved_by=%s, resolved_at=now() WHERE ticket_id=%s",
                      (Jsonb(choice), Jsonb(identity), ticket_id))
        self.pg.conn.commit()
        return out

    def open_tickets(self, token):
        self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT ticket_id, verb, reason, options FROM decision_tickets "
                      "WHERE status='open' ORDER BY ticket_id")
            return [{"ticket": t, "verb": v, "reason": r, "options": o}
                    for t, v, r, o in c.fetchall()]

    # -- requests (the crowdsourcing loop; user rulings 2026-08-09) ------------
    # Workflow, never facts. Kinds are the arch's own wants: WANT_NODE /
    # WANT_COVERAGE / WANT_EVIDENCE. Close on fulfill (never wait on absent
    # people); anyone may re-open. Karma: fulfiller 3 + endorsements, poster 1.

    def post_request(self, token, want, subject_node=None, wanted_name=None,
                     wanted_description=None, notes=None, offered_sources=None):
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if want not in ("WANT_NODE", "WANT_COVERAGE", "WANT_EVIDENCE"):
            return {"rejected": {"rule": "REQ", "message":
                    "want must be WANT_NODE | WANT_COVERAGE | WANT_EVIDENCE"}}
        if want == "WANT_NODE" and not wanted_name:
            return {"rejected": {"rule": "REQ",
                                 "message": "WANT_NODE needs wanted_name"}}
        if want != "WANT_NODE":
            _, view = self._kernel()
            if not subject_node or not view.node(subject_node):
                return {"rejected": {"rule": "REQ", "message":
                        f"{want} needs an existing subject_node"}}
        with self.pg.conn.cursor() as c:
            c.execute(
                "INSERT INTO requests (want, subject_node, wanted_name, "
                "wanted_description, notes, offered_sources, requested_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING request_id",
                (want, subject_node, wanted_name, wanted_description, notes,
                 Jsonb(offered_sources or []), Jsonb(identity)))
            rid = c.fetchone()[0]
        return {"request": rid}

    def list_requests(self, token, status="open"):
        self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute(
                "SELECT r.request_id, r.want, r.subject_node, r.wanted_name, "
                "r.wanted_description, r.notes, r.offered_sources, r.status, "
                "r.requested_by, r.fulfilled_by, r.fulfilled_links, "
                "(SELECT count(*) FROM request_endorsements e "
                " WHERE e.request_id = r.request_id) AS endorsements "
                "FROM requests r WHERE (%s = 'all' OR r.status = %s "
                "  OR (%s = 'open' AND r.status = 'reopened')) "
                "ORDER BY endorsements DESC, r.request_id",
                (status, status, status))
            cols = ("request", "want", "subject_node", "wanted_name",
                    "wanted_description", "notes", "offered_sources", "status",
                    "requested_by", "fulfilled_by", "fulfilled_links",
                    "endorsements")
            return [dict(zip(cols, row)) for row in c.fetchall()]

    def endorse_request(self, token, request_id):
        identity, _ = self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT status FROM requests WHERE request_id=%s",
                      (request_id,))
            row = c.fetchone()
            if not row:
                return {"rejected": {"rule": "E404",
                                     "message": f"request {request_id}?"}}
            c.execute("INSERT INTO request_endorsements (request_id, endorser) "
                      "VALUES (%s,%s) ON CONFLICT DO NOTHING",
                      (request_id, identity.get("id")))
        return {"endorsed": request_id}

    def fulfill_request(self, token, request_id, links, note=None):
        """Close NOW (user ruling: never wait on slow/absent requesters);
        anyone can re-open. links = the node/edge/assertion ids that satisfy."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if not links:
            return {"rejected": {"rule": "REQ",
                                 "message": "fulfillment must link what was "
                                            "built (node/edge/assertion ids)"}}
        with self.pg.conn.cursor() as c:
            c.execute("SELECT status, requested_by FROM requests "
                      "WHERE request_id=%s", (request_id,))
            row = c.fetchone()
            if not row:
                return {"rejected": {"rule": "E404",
                                     "message": f"request {request_id}?"}}
            if row[0] not in ("open", "reopened"):
                return {"rejected": {"rule": "REQ", "message": "already fulfilled"}}
            requested_by = row[1]
            c.execute("SELECT count(*) FROM request_endorsements "
                      "WHERE request_id=%s", (request_id,))
            endorsements = c.fetchone()[0]
            c.execute("UPDATE requests SET status='fulfilled', fulfilled_by=%s, "
                      "fulfilled_links=%s, fulfilled_at=now(), "
                      "notes=COALESCE(%s, notes) WHERE request_id=%s",
                      (Jsonb(identity), Jsonb(links), note, request_id))
            pts = 3 + endorsements
            c.execute("UPDATE users SET ink = ink + %s WHERE user_id = %s",
                      (pts, identity.get("id")))
            c.execute("UPDATE users SET ink = ink + 1 WHERE user_id = %s",
                      (requested_by.get("id"),))
        return {"fulfilled": request_id, "points_earned": pts}

    def reopen_request(self, token, request_id, reason):
        identity, _ = self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("UPDATE requests SET status='reopened', "
                      "notes = COALESCE(notes,'') || %s WHERE request_id=%s "
                      "AND status='fulfilled' RETURNING request_id",
                      (f"\n[re-opened by {identity.get('id')}: {reason}]",
                       request_id))
            row = c.fetchone()
        if not row:
            return {"rejected": {"rule": "REQ",
                                 "message": "not found or not fulfilled"}}
        return {"reopened": request_id}

    def deletion_records(self, token, k=100):
        """The PUBLIC removal record (ADR-0047 §5): every tombstone with who
        marked it, who approved it, and why. Off the map, never off the books."""
        self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT seq, kind, body, author, wall_time FROM facts "
                      "WHERE kind IN ('node.tombstone','edge.tombstone') "
                      "ORDER BY seq DESC LIMIT %s", (k,))
            stones = [{"seq": s, "kind": kd.split(".")[0],
                       "subject": b.get("node_id") or b.get("edge_id"),
                       "reason": b.get("reason", ""),
                       "approved_by": a.get("id"), "at": wt.isoformat()}
                      for s, kd, b, a, wt in c.fetchall()]
            c.execute("SELECT params, opened_by FROM decision_tickets "
                      "WHERE verb IN ('delete','delete_node')")
            marked = {(p.get("subject") or p.get("node_id")): ob.get("id")
                      for p, ob in c.fetchall()}
        for st in stones:
            st["marked_by"] = marked.get(st["subject"])
        return stones

    def leaderboard(self, token, k=20):
        """Karma + reputation + lifetime contribution counts — the user
        database's public face (everything public, user ruling 2026-08-09)."""
        self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute(
                "SELECT u.user_id, u.kind, u.operator, u.ink, u.reputation, "
                "       COALESCE(f.n, 0) AS facts "
                "FROM users u LEFT JOIN "
                "  (SELECT author->>'id' AS id, count(*) AS n FROM facts "
                "   GROUP BY author->>'id') f ON f.id = u.user_id "
                "ORDER BY u.ink DESC, facts DESC LIMIT %s", (k,))
            return [{"id": i, "type": t, "operator": op, "ink": ka,
                     "reputation": rep, "facts": n}
                    for i, t, op, ka, rep, n in c.fetchall()]

    def contributions(self, token, identity_id, k=40):
        """Everything an identity did — free, because every fact is stamped
        (ADR-0041/0042: blame to people). Clickable history for the tab."""
        self.authenticate(token)
        out = {"id": identity_id}
        with self.pg.conn.cursor() as c:
            c.execute("SELECT kind, operator, ink, reputation, bio, link "
                      "FROM users WHERE user_id=%s", (identity_id,))
            row = c.fetchone()
            if row:
                out.update(kind=row[0], operator=row[1], ink=row[2],
                           reputation=row[3], bio=row[4], link=row[5])
            else:
                out.update(kind=None, operator=None, ink=0, reputation=0)
            c.execute("SELECT user_id FROM users WHERE operator=%s "
                      "ORDER BY user_id", (identity_id,))
            out["operates"] = [r[0] for r in c.fetchall()]
            c.execute("SELECT kind, count(*) FROM facts "
                      "WHERE author->>'id'=%s GROUP BY kind", (identity_id,))
            out["counts"] = dict(c.fetchall())
            c.execute("SELECT seq, kind, body, wall_time FROM facts "
                      "WHERE author->>'id'=%s ORDER BY seq DESC LIMIT %s",
                      (identity_id, k))
            acts = []
            for seq, kind, body, wt in c.fetchall():
                if kind == "node.create":
                    line, subj = f"created node {body.get('node_id')}", body.get("node_id")
                elif kind == "edge.create":
                    line = (f"linked {body.get('from')} → {body.get('to')} "
                            f"({body.get('type')})")
                    subj = body.get("to")
                elif kind == "assert":
                    line, subj = (f"asserted {body.get('field')} on "
                                  f"{body.get('subject')}", body.get("subject"))
                elif kind == "cite":
                    line, subj = "attached a citation", None
                else:
                    line, subj = kind, None
                acts.append({"seq": seq, "line": line, "subject": subj,
                             "at": wt.isoformat()})
            out["recent"] = acts
            c.execute("SELECT request_id, want, subject_node, wanted_name "
                      "FROM requests WHERE fulfilled_by->>'id'=%s "
                      "ORDER BY request_id DESC", (identity_id,))
            out["fulfilled"] = [{"request": r, "want": w,
                                 "about": sn or wn}
                                for r, w, sn, wn in c.fetchall()]
        return out

    # -- verification & challenges (ADR-0049; events are FACTS) ----------------
    def _all_facts(self):
        with self.pg.conn.cursor() as c:
            c.execute("SELECT fact_id, kind, author, body FROM facts ORDER BY seq")
            return [{"fact_id": f, "kind": k, "author": a, "body": b}
                    for f, k, a, b in c.fetchall()]

    def _refresh_reputation(self):
        """users.reputation is a CACHE of compute(fact log) — never authored."""
        with self.pg.conn.cursor() as c:
            c.execute("SELECT user_id, operator FROM users WHERE operator IS NOT NULL")
            operators = dict(c.fetchall())
        rep = reputation.compute(self._all_facts(), operators)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT user_id FROM users")
            for (uid,) in c.fetchall():
                c.execute("UPDATE users SET reputation=%s, "
                          "max_reputation=GREATEST(max_reputation, %s) "
                          "WHERE user_id=%s",
                          (rep.get(uid, 0), rep.get(uid, 0), uid))

    def _assertion_exists(self, assertion_id):
        with self.pg.conn.cursor() as c:
            c.execute("SELECT 1 FROM facts WHERE fact_id=%s AND kind='assert'",
                      (assertion_id,))
            return c.fetchone() is not None

    def verify_citation(self, token, assertion_id, verdict, model=None, note=None):
        """L2→L3 machine verification event (ADR-0032/0049). verdict:
        supported | unsupported | hallucinated."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if verdict not in ("supported", "unsupported", "hallucinated"):
            return {"rejected": {"rule": "ADR-0032", "message": "bad verdict"}}
        if not self._assertion_exists(assertion_id):
            return {"rejected": {"rule": "E404", "message": f"{assertion_id}?"}}
        out = self._apply(identity, [("verification.machine",
                                      {"assertion_id": assertion_id,
                                       "verdict": verdict,
                                       "model": model or identity.get("model"),
                                       "note": note})], [])
        self._refresh_reputation()
        return out

    def confirm_verification(self, token, assertion_id, verdict, note=None):
        """L3→L4 human confirmation (humans only — that's the rung's meaning)."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if identity.get("type") != "human":
            return {"rejected": {"rule": "ADR-0032",
                                 "message": "L4 confirmations are human-only"}}
        if verdict not in ("supported", "unsupported"):
            return {"rejected": {"rule": "ADR-0032", "message": "bad verdict"}}
        if not self._assertion_exists(assertion_id):
            return {"rejected": {"rule": "E404", "message": f"{assertion_id}?"}}
        out = self._apply(identity, [("verification.human",
                                      {"assertion_id": assertion_id,
                                       "verdict": verdict, "note": note})], [])
        self._refresh_reputation()
        return out

    def open_challenge(self, token, subject, grounds, remedy=None):
        """A structured dispute (ADR-0049 §7): subject + grounds + optional
        pre-staged remedy verbs [{verb, params}]. Votes advise; ADMIN ratifies."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        _, view = self._kernel()
        if not (view.node(subject) or view.edge(subject)
                or self._assertion_exists(subject)):
            return {"rejected": {"rule": "E404", "message": f"{subject}?"}}
        if not grounds:
            return {"rejected": {"rule": "ADR-0049",
                                 "message": "a challenge needs grounds"}}
        out = self._apply(identity, [("challenge.open",
                                      {"subject": subject, "grounds": grounds,
                                       "remedy": remedy or [],
                                       "opened_by": identity.get("id")})], [])
        out["challenge"] = out["applied"]["created"]["assertions"] or None
        with self.pg.conn.cursor() as c:      # the open fact's id IS the handle
            c.execute("SELECT fact_id FROM facts WHERE kind='challenge.open' "
                      "ORDER BY seq DESC LIMIT 1")
            out["challenge"] = c.fetchone()[0]
        return out

    def vote_challenge(self, token, challenge_id, support, reason):
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if not reason:
            return {"rejected": {"rule": "ADR-0049",
                                 "message": "votes carry reasons"}}
        ch = next((f for f in self._all_facts()
                   if f["fact_id"] == challenge_id
                   and f["kind"] == "challenge.open"), None)
        if ch is None:
            return {"rejected": {"rule": "E404", "message": f"{challenge_id}?"}}
        return self._apply(identity, [("challenge.vote",
                                       {"challenge_id": challenge_id,
                                        "support": bool(support),
                                        "reason": reason})], [])

    def challenge_tally(self, token, challenge_id):
        """Weighted tally (advisory): weight = 1 + max(0, reputation), vested
        voters only (ADR-0049 §4); unvested votes are recorded but weigh 0."""
        self.authenticate(token)
        facts = self._all_facts()
        with self.pg.conn.cursor() as c:
            c.execute("SELECT user_id, reputation FROM users")
            rep = dict(c.fetchall())
        tally = {"support": 0.0, "oppose": 0.0, "votes": []}
        seen = set()
        for f in reversed(facts):            # latest vote per identity wins
            if f["kind"] != "challenge.vote":
                continue
            b = f["body"]
            if b.get("challenge_id") != challenge_id:
                continue
            who = f["author"].get("id")
            if who in seen:
                continue
            seen.add(who)
            is_vested = reputation.vested(facts, who) or False
            with self.pg.conn.cursor() as c:
                c.execute("SELECT is_admin FROM users WHERE user_id=%s", (who,))
                row = c.fetchone()
                if row and row[0]:
                    is_vested = True
            w = (1 + max(0, rep.get(who, 0))) if is_vested else 0
            tally["support" if b["support"] else "oppose"] += w
            tally["votes"].append({"by": who, "support": b["support"],
                                   "weight": w, "vested": is_vested,
                                   "reason": b.get("reason")})
        return tally

    def resolve_challenge(self, token, challenge_id, outcome,
                          demoted=None, note=None):
        """ADMIN ratifies (user ruling): outcome upheld|rejected. On upheld,
        pre-staged remedy verbs execute under the resolver's identity with the
        challenge as provenance; `demoted` assertion ids feed the rep engine."""
        identity, budget = self.authenticate(token)
        self._check_budget(identity, budget)
        if not identity.get("admin"):
            return {"rejected": {"rule": "ADMIN",
                                 "message": "challenges are ratified by admins"}}
        if outcome not in ("upheld", "rejected"):
            return {"rejected": {"rule": "ADR-0049", "message": "bad outcome"}}
        ch = next((f for f in self._all_facts()
                   if f["fact_id"] == challenge_id
                   and f["kind"] == "challenge.open"), None)
        if ch is None:
            return {"rejected": {"rule": "E404", "message": f"{challenge_id}?"}}
        out = self._apply(identity, [("challenge.resolve",
                                      {"challenge_id": challenge_id,
                                       "outcome": outcome,
                                       "opened_by": ch["body"].get("opened_by"),
                                       "demoted": demoted or [],
                                       "note": note})], [])
        remedy_results = []
        if outcome == "upheld":
            # remedies run VERBATIM — the challenge.resolve fact is already
            # the provenance for every one of them
            for r in ch["body"].get("remedy", []):
                remedy_results.append(
                    {"verb": r.get("verb"),
                     "result": self.execute(token, r.get("verb"),
                                            dict(r.get("params", {})))})
        self._refresh_reputation()
        out["remedy_results"] = remedy_results
        return out

    def list_challenges(self, token):
        self.authenticate(token)
        facts = self._all_facts()
        resolved = {f["body"]["challenge_id"]: f["body"]["outcome"]
                    for f in facts if f["kind"] == "challenge.resolve"}
        out = []
        for f in facts:
            if f["kind"] != "challenge.open":
                continue
            out.append({"challenge": f["fact_id"], "subject": f["body"]["subject"],
                        "grounds": f["body"]["grounds"],
                        "remedy": f["body"].get("remedy", []),
                        "opened_by": f["body"].get("opened_by"),
                        "status": resolved.get(f["fact_id"], "open")})
        return out

    # -- structure linters (the graph files bounties on itself) ----------------
    def run_sibling_linter(self, min_shared=5):
        """Sibling clusters (user's Samsung-Galaxy case): nodes sharing ≥
        min_shared providers with no common taxonomy parent get a WANT_NODE
        request auto-posted by the 'linter' system identity — agents discover
        structural debt through the same bounty queue as human asks."""
        _, view = self._kernel()
        from httk.store import HARD_TYPES, TAXONOMY_TYPES
        claims, parents = {}, {}
        for n in view.nodes():
            if view.edges_out(n, {"IS_REFINEMENT_OF"}):
                continue                     # versions cluster by design
            claims[n] = {(e["from"], e["type"])
                         for e in view.edges_in(n, HARD_TYPES)
                         if not view.is_shadowed(e["edge_id"])}
            parents[n] = {e["to"] for e in view.edges_out(n, TAXONOMY_TYPES)}
        posted = []
        nodes = sorted(claims)
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                shared = claims[a] & claims[b]
                if len(shared) < min_shared or (parents[a] & parents[b]):
                    continue
                wanted = f"Taxonomy parent for {a} + {b}"
                with self.pg.conn.cursor() as c:
                    c.execute("SELECT 1 FROM requests WHERE wanted_name=%s "
                              "AND status IN ('open','reopened')", (wanted,))
                    if c.fetchone():
                        continue
                    c.execute(
                        "INSERT INTO requests (want, wanted_name, "
                        "wanted_description, notes, requested_by) "
                        "VALUES ('WANT_NODE', %s, %s, %s, %s)",
                        (wanted,
                         f"A family node both {a} and {b} are types of; "
                         "extract_family hoists the shared dependencies.",
                         "auto-posted by the sibling-cluster linter; shared: "
                         + ", ".join(sorted(f"{p} ({t})" for p, t in shared)),
                         Jsonb({"type": "system", "id": "linter"})))
                posted.append(wanted)
        return {"posted": posted}

    # -- internals -------------------------------------------------------------
    def _apply(self, identity, facts, notes):
        cr = self.pg.open_cr(proposer=identity)
        for kind, body in facts:
            cr.add(kind, body)
        status, flags, created = self.pg.apply(cr)
        # echo what was made (agent friction #2): node/edge ids and — crucially
        # — assertion ids, which attach_citation needs and nothing returned
        echo = {"nodes": [c["id"] for c in created if c["kind"] == "node.create"],
                "edges": [c["id"] for c in created if c["kind"] == "edge.create"],
                "assertions": [{"assertion_id": c["fact_id"],
                                "subject": c["subject"], "field": c["field"]}
                               for c in created if c["kind"] == "assert"]}
        return {"applied": {"cr": cr.cr_id, "status": status, "flags": flags,
                            "facts_written": len(facts), "notes": notes,
                            "created": echo}}

    def _open_ticket(self, identity, verb, params, reason, options, evidence=None):
        with self.pg.conn.cursor() as c:
            c.execute("INSERT INTO decision_tickets (verb, params, reason, options, "
                      "opened_by) VALUES (%s,%s,%s,%s,%s) RETURNING ticket_id",
                      (verb, Jsonb(params), reason, Jsonb(options), Jsonb(identity)))
            t = c.fetchone()[0]
        self.pg.conn.commit()
        return {"ticket": t, "reason": reason, "options": options,
                "evidence": evidence or {}}
