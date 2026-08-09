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
        with self.pg.conn.cursor() as c:
            c.execute(
                "INSERT INTO identities (token_hash, identity, budget_per_hour) "
                "VALUES (%s,%s,%s) ON CONFLICT (token_hash) DO UPDATE "
                "SET identity=EXCLUDED.identity, budget_per_hour=EXCLUDED.budget_per_hour",
                (self.hash_token(token), Jsonb(identity), budget_per_hour))
        self.pg.conn.commit()

    def authenticate(self, token):
        with self.pg.conn.cursor() as c:
            c.execute("SELECT identity, budget_per_hour FROM identities "
                      "WHERE token_hash=%s", (self.hash_token(token),))
            row = c.fetchone()
        if not row:
            raise AuthError("unknown credential")
        return row[0], row[1]

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
        """Deterministic v1 gate: name/alias matching → receipt. Semantic upgrade
        (Luna/Tera-class judge) slots behind this same tool later (ADR-0041 §4)."""
        identity, _ = self.authenticate(token)
        _, view = self._kernel()
        q = query.lower()
        hits = []
        for n in view.nodes():
            names = [n, view.field(n, "name") or ""] + (view.field(n, "aliases", []) or [])
            if any(q == str(x).lower() or q in str(x).lower() for x in names if x):
                hits.append({"node_id": n, "category": view.node(n)["category"]})
        with self.pg.conn.cursor() as c:
            c.execute("INSERT INTO search_receipts (query, results, issued_to) "
                      "VALUES (%s,%s,%s) RETURNING receipt_id",
                      (query, Jsonb(hits), Jsonb(identity)))
            rid = c.fetchone()[0]
        self.pg.conn.commit()
        return {"receipt": rid, "matches": hits}

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
        _, matches = row
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
        MARKERS = {"justification_required"}

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
        if verb == "propose_node":
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
                "FROM requests r WHERE (%s = 'all' OR r.status = %s) "
                "ORDER BY endorsements DESC, r.request_id", (status, status))
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
            if row[0] != "open":
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
            c.execute("UPDATE identities SET points = points + %s "
                      "WHERE identity->>'id' = %s", (pts, identity.get("id")))
            c.execute("UPDATE identities SET points = points + 1 "
                      "WHERE identity->>'id' = %s", (requested_by.get("id"),))
        return {"fulfilled": request_id, "points_earned": pts}

    def reopen_request(self, token, request_id, reason):
        identity, _ = self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("UPDATE requests SET status='open', "
                      "notes = COALESCE(notes,'') || %s WHERE request_id=%s "
                      "AND status='fulfilled' RETURNING request_id",
                      (f"\n[re-opened by {identity.get('id')}: {reason}]",
                       request_id))
            row = c.fetchone()
        if not row:
            return {"rejected": {"rule": "REQ",
                                 "message": "not found or not fulfilled"}}
        return {"reopened": request_id}

    def leaderboard(self, token, k=20):
        self.authenticate(token)
        with self.pg.conn.cursor() as c:
            c.execute("SELECT identity->>'id', identity->>'type', points "
                      "FROM identities WHERE points > 0 "
                      "ORDER BY points DESC LIMIT %s", (k,))
            return [{"id": i, "type": t, "points": p} for i, t, p in c.fetchall()]

    # -- internals -------------------------------------------------------------
    def _apply(self, identity, facts, notes):
        cr = self.pg.open_cr(proposer=identity)
        for kind, body in facts:
            cr.add(kind, body)
        status, flags = self.pg.apply(cr)
        return {"applied": {"cr": cr.cr_id, "status": status, "flags": flags,
                            "facts_written": len(facts), "notes": notes}}

    def _open_ticket(self, identity, verb, params, reason, options, evidence=None):
        with self.pg.conn.cursor() as c:
            c.execute("INSERT INTO decision_tickets (verb, params, reason, options, "
                      "opened_by) VALUES (%s,%s,%s,%s,%s) RETURNING ticket_id",
                      (verb, Jsonb(params), reason, Jsonb(options), Jsonb(identity)))
            t = c.fetchone()[0]
        self.pg.conn.commit()
        return {"ticket": t, "reason": reason, "options": options,
                "evidence": evidence or {}}
