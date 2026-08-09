"""The Postgres fact log: append-only writes, ChangeRequest apply semantics, JSONL
export — shaped EXACTLY like the kernel's Store facts so the kernel solver runs
unchanged over a DB export (one semantics, two substrates).

Apply semantics (SCHEMA §8):
- CR-apply is one transaction inserting immutable assertion facts (commutative
  set-union; distinct facts in any order converge — ADR-0023/0031).
- B4 (H4): a merge-redirect assertion whose target chain reaches the source is a
  HARD reject at apply (the CR does not merge; BreakerViolation).
- H9: structural breakers (B1 hard-dependency cycles) re-run AFTER the merge in
  the same transaction; joint violations FLAG the CR (status='flagged', facts
  stay — flags, never reorders) and are surfaced for review.
- Retraction is a forward fact; projections recompute the affected field.
"""
import json
import os

import psycopg
from psycopg.types.json import Jsonb

HARD_TYPES = {"ENABLES", "IS_COMPONENT_OF", "IS_INGREDIENT_OF"}


class BreakerViolation(Exception):
    pass


class ChangeRequest:
    """A shadow branch: staged assertions, applied atomically (ADR-0013/0031)."""

    def __init__(self, cr_id, proposer):
        self.cr_id = cr_id
        self.proposer = proposer
        self.staged = []  # list of (kind, body)

    def add(self, kind, body):
        self.staged.append((kind, body))
        return self

    # authoring sugar mirroring the kernel Store API
    def create_node(self, node_id, category="TECHNOLOGY", validity="current_truth"):
        self.add("node.create", {"node_id": node_id, "category": category})
        self.assert_field(node_id, "validity", validity)
        return node_id

    def create_edge(self, edge_id, frm, to, etype, qualifier=None):
        self.add("edge.create", {"edge_id": edge_id, "from": frm, "to": to,
                                 "type": etype, "qualifier": qualifier})
        return edge_id

    def assert_field(self, subject, field, value):
        self.add("assert", {"subject": subject, "field": field, "value": value})

    def retract(self, assertion_fact_id):
        self.add("retract", {"target": assertion_fact_id})

    def cite(self, claim_assertion_id, source_node, locator=None):
        self.add("cite", {"claim": claim_assertion_id, "source": source_node,
                          "locator": locator})


class PgFactLog:
    def __init__(self, dsn=None):
        self.dsn = dsn or os.environ.get(
            "HTT_PG_DSN", "postgresql://postgres:httk@localhost:5433/httk")
        # autocommit: reads must NEVER leave the connection idle-in-transaction
        # (a long-lived tiler holding ACCESS SHARE on facts blocks any
        # ALTER/TRUNCATE forever). Multi-statement writes open explicit
        # transactions via conn.transaction().
        self.conn = psycopg.connect(self.dsn, autocommit=True)

    # -- lifecycle -----------------------------------------------------------
    def migrate(self, sql_path):
        with open(sql_path, encoding="utf-8") as f:
            sql = f.read()
        with self.conn.transaction(), self.conn.cursor() as cur:
            cur.execute(sql)

    def wipe(self):
        with self.conn.transaction(), self.conn.cursor() as cur:
            for t in ("citations", "current_fields", "edge_identities",
                      "node_identities", "change_requests", "facts"):
                cur.execute(f"TRUNCATE {t} RESTART IDENTITY CASCADE")

    def close(self):
        self.conn.close()

    # -- ChangeRequests ------------------------------------------------------
    def open_cr(self, proposer=None):
        proposer = proposer or {"type": "system", "id": "ref"}
        with self.conn.transaction(), self.conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(seq),0) FROM facts")
            n = cur.fetchone()[0]
            cr_id = f"cr_{n + 1:06d}_{abs(hash(json.dumps(proposer, sort_keys=True))) % 997}"
            cur.execute(
                "INSERT INTO change_requests (cr_id, proposer, status) VALUES (%s,%s,'draft')",
                (cr_id, Jsonb(proposer)))
        return ChangeRequest(cr_id, proposer)

    def apply(self, cr):
        """One transaction: breakers → insert facts → projections → post-merge recheck."""
        try:
            with self.conn.transaction(), self.conn.cursor() as cur:
                # B4 (H4): merge-redirect acyclicity is a HARD apply-time breaker
                for kind, body in cr.staged:
                    if kind == "assert" and body["field"] == "migrated_to" and body["value"]:
                        self._walk_redirect_guard(cur, body["subject"], body["value"])

                for kind, body in cr.staged:
                    cur.execute(
                        "INSERT INTO facts (fact_id, kind, author, cr_id, body) "
                        "VALUES ('pending', %s, %s, %s, %s) RETURNING seq",
                        (kind, Jsonb(cr.proposer), cr.cr_id, Jsonb(body)))
                    seq = cur.fetchone()[0]
                    fact_id = f"f_{seq:05d}"
                    cur.execute("UPDATE facts SET fact_id=%s WHERE seq=%s", (fact_id, seq))
                    self._project(cur, seq, fact_id, kind, body)

                # H9: post-merge structural recheck — flags, never reorders
                flags = self._hard_cycles(cur)
                status = "flagged" if flags else "merged"
                cur.execute(
                    "UPDATE change_requests SET status=%s, flags=%s, "
                    "merged_seq=(SELECT MAX(seq) FROM facts) WHERE cr_id=%s",
                    (status, Jsonb(flags), cr.cr_id))
            return status, flags
        except BreakerViolation:
            with self.conn.cursor() as c2:
                c2.execute("UPDATE change_requests SET status='flagged', "
                           "flags=%s WHERE cr_id=%s",
                           (Jsonb(["B4: redirect cycle"]), cr.cr_id))
            raise

    # -- convenience: single-fact system CRs (tests/seeding) ------------------
    def quick(self, build):
        cr = self.open_cr()
        build(cr)
        return self.apply(cr)

    # -- projections ----------------------------------------------------------
    def _project(self, cur, seq, fact_id, kind, body):
        if kind == "node.create":
            cur.execute(
                "INSERT INTO node_identities (node_id, category, created_seq) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (body["node_id"], body["category"], seq))
        elif kind == "edge.create":
            cur.execute(
                "INSERT INTO edge_identities (edge_id, from_node, to_node, type, "
                "qualifier, created_seq) VALUES (%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT DO NOTHING",
                (body["edge_id"], body["from"], body["to"], body["type"],
                 body.get("qualifier"), seq))
        elif kind == "assert":
            cur.execute(
                "INSERT INTO current_fields (subject_id, field_path, value, "
                "assertion_fact_id, seq) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (subject_id, field_path) DO UPDATE SET "
                "value=EXCLUDED.value, assertion_fact_id=EXCLUDED.assertion_fact_id, "
                "seq=EXCLUDED.seq WHERE current_fields.seq < EXCLUDED.seq",
                (body["subject"], body["field"], Jsonb(body["value"]), fact_id, seq))
        elif kind == "node.tombstone":
            # ADR-0047: projections drop the node + incident edges; the log
            # keeps everything (as-of reads before the tombstone still see it)
            cur.execute("DELETE FROM edge_identities WHERE from_node=%s "
                        "OR to_node=%s", (body["node_id"], body["node_id"]))
            cur.execute("DELETE FROM node_identities WHERE node_id=%s",
                        (body["node_id"],))
        elif kind == "edge.tombstone":
            cur.execute("DELETE FROM edge_identities WHERE edge_id=%s",
                        (body["edge_id"],))
        elif kind == "retract":
            self._recompute_field_for(cur, body["target"])
        elif kind == "cite":
            cur.execute(
                "INSERT INTO citations (claim_assertion_id, source_node, locator, seq) "
                "VALUES (%s,%s,%s,%s)",
                (body["claim"], body["source"], body.get("locator"), seq))

    def _recompute_field_for(self, cur, target_fact_id):
        cur.execute("SELECT body FROM facts WHERE fact_id=%s AND kind='assert'",
                    (target_fact_id,))
        row = cur.fetchone()
        if not row:
            return
        subject, fpath = row[0]["subject"], row[0]["field"]
        cur.execute(
            "SELECT f.fact_id, f.body, f.seq FROM facts f WHERE f.kind='assert' "
            "AND f.body->>'subject'=%s AND f.body->>'field'=%s "
            "AND NOT EXISTS (SELECT 1 FROM facts r WHERE r.kind='retract' "
            "                AND r.body->>'target'=f.fact_id) "
            "ORDER BY f.seq DESC LIMIT 1", (subject, fpath))
        latest = cur.fetchone()
        if latest:
            cur.execute(
                "UPDATE current_fields SET value=%s, assertion_fact_id=%s, seq=%s "
                "WHERE subject_id=%s AND field_path=%s",
                (Jsonb(latest[1]["value"]), latest[0], latest[2], subject, fpath))
        else:
            cur.execute("DELETE FROM current_fields WHERE subject_id=%s AND field_path=%s",
                        (subject, fpath))

    def rebuild_projections(self):
        """Replay the log — proves projections are pure indexes over it."""
        with self.conn.transaction(), self.conn.cursor() as cur:
            for t in ("citations", "current_fields", "edge_identities", "node_identities"):
                cur.execute(f"TRUNCATE {t} CASCADE")
            cur.execute("SELECT seq, fact_id, kind, body FROM facts ORDER BY seq")
            for seq, fact_id, kind, body in cur.fetchall():
                self._project(cur, seq, fact_id, kind, body)

    # -- breakers -------------------------------------------------------------
    def _walk_redirect_guard(self, cur, src, dst):
        seen, cur_node = set(), dst
        while cur_node:
            if cur_node == src or cur_node in seen:
                raise BreakerViolation(f"B4: redirect {src}->{dst} closes a cycle")
            seen.add(cur_node)
            cur.execute("SELECT value FROM current_fields WHERE subject_id=%s "
                        "AND field_path='migrated_to'", (cur_node,))
            row = cur.fetchone()
            cur_node = row[0] if row and row[0] else None

    def _hard_cycles(self, cur):
        cur.execute("SELECT from_node, to_node FROM edge_identities WHERE type = ANY(%s)",
                    (list(HARD_TYPES),))
        graph = {}
        for frm, to in cur.fetchall():
            graph.setdefault(to, []).append(frm)   # consumer -> providers
        WHITE, GRAY, BLACK = 0, 1, 2
        color, flags = {}, []

        def dfs(n, path):
            color[n] = GRAY
            for m in graph.get(n, []):
                if color.get(m, WHITE) == GRAY:
                    flags.append(f"B1/H9: hard dependency cycle near {m}")
                elif color.get(m, WHITE) == WHITE:
                    dfs(m, path + [m])
            color[n] = BLACK

        for n in list(graph):
            if color.get(n, WHITE) == WHITE:
                dfs(n, [n])
        return flags

    # -- the canonical export (SCHEMA §9) -------------------------------------
    def export_jsonl(self):
        """Kernel-shaped lines: the kernel solver runs unchanged over this."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT seq, fact_id, kind, author, body FROM facts ORDER BY seq")
            lines = []
            for seq, fact_id, kind, author, body in cur.fetchall():
                lines.append(json.dumps(
                    {"fact_id": fact_id, "kind": kind, "recorded_at": seq,
                     "author": author, "body": body}, sort_keys=True))
        return "\n".join(lines)
