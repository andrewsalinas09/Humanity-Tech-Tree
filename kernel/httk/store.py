"""Append-only assertion store with identity/assertion split and as-of resolution.

ADR-0026: only ground facts are stored; ADR-0038: identities (node_id/edge_id, enduring,
what semantics reference) vs assertions (dated statements, what evidence references);
ADR-0034: record time is a monotone logical clock, every read can be as-of;
ADR-0011: nothing is deleted — corrections supersede, retraction is a new fact;
H4: merge redirects walk to fixpoint; cycles are a circuit-breaker violation.
"""
import json


HARD_TYPES = {"ENABLES", "IS_COMPONENT_OF", "IS_INGREDIENT_OF"}
TAXONOMY_TYPES = {"IS_TYPE_OF", "IS_REFINEMENT_OF"}
ALL_TYPES = HARD_TYPES | TAXONOMY_TYPES | {"OPTIMIZES", "SUCCEEDS", "ASSOCIATION"}


class BreakerViolation(Exception):
    """A circuit breaker (B1..B4) rejected an operation."""


class Store:
    """The fact log. Every append returns a stable fact_id (= assertion_id, ADR-0038)."""

    def __init__(self):
        self.facts = []

    # -- raw log ------------------------------------------------------------
    def append(self, kind, body, author="ref"):
        fid = f"f_{len(self.facts) + 1:05d}"
        self.facts.append({
            "fact_id": fid, "kind": kind, "recorded_at": len(self.facts) + 1,
            "author": author, "body": body,
        })
        return fid

    def dump(self):
        return "\n".join(json.dumps(f, sort_keys=True) for f in self.facts)

    @classmethod
    def load(cls, jsonl):
        s = cls()
        s.facts = [json.loads(line) for line in jsonl.splitlines() if line.strip()]
        return s

    # -- authoring helpers (identity creation + field assertions) -----------
    # NOTE: the validity default here is TEST SCAFFOLDING standing in for an
    # explicit author choice. The public surface (propose_node) has NO default:
    # unstated validity stays absent — blame corollary, ADR-0042.
    def create_node(self, node_id, category="TECHNOLOGY", validity="current_truth"):
        self.append("node.create", {"node_id": node_id, "category": category})
        self.assert_field(node_id, "validity", validity)
        return node_id

    def create_edge(self, edge_id, frm, to, etype, qualifier=None):
        """Edge identity: from/to/type are immutable (endpoint change = NEW identity,
        ADR-0038 / TB-068). Everything else about the edge is field assertions."""
        assert etype in ALL_TYPES, etype
        self.append("edge.create", {
            "edge_id": edge_id, "from": frm, "to": to, "type": etype,
            "qualifier": qualifier,
        })
        return edge_id

    def assert_field(self, subject, field, value):
        """Supersedes any earlier assertion for (subject, field) — latest-at-T wins."""
        return self.append("assert", {"subject": subject, "field": field, "value": value})

    def retract(self, assertion_id):
        """Retraction is a forward fact (ADR-0011); the target stays in history."""
        return self.append("retract", {"target": assertion_id})

    def merge(self, src, dst):
        """MIGRATED_TO redirect with the H4 acyclicity breaker at apply time."""
        view = View(self)
        chain_end = view.resolve_redirect(dst, _allow_missing=True)
        if chain_end == src:
            raise BreakerViolation(f"B4: redirect {src}->{dst} closes a cycle")
        return self.assert_field(src, "migrated_to", dst)

    def unmerge(self, src):
        """H5: forward-edit reversal — reopens src; history keeps both facts."""
        return self.assert_field(src, "migrated_to", None)


class View:
    """As-of resolution over the log. at=None means 'now' (all facts)."""

    def __init__(self, store, at=None):
        self.at = at if at is not None else len(store.facts) + 1
        self._nodes, self._edges, self._fields = {}, {}, {}
        retracted = set()
        for f in store.facts:
            if f["recorded_at"] > self.at:
                continue
            b, k = f["body"], f["kind"]
            if k == "retract":
                retracted.add(b["target"])
        for f in store.facts:
            if f["recorded_at"] > self.at or f["fact_id"] in retracted:
                continue
            b, k = f["body"], f["kind"]
            if k == "node.create":
                self._nodes[b["node_id"]] = dict(b)
            elif k == "edge.create":
                self._edges[b["edge_id"]] = dict(b)
            elif k == "assert":
                # latest-at-T wins per (subject, field): facts are in record order
                self._fields[(b["subject"], b["field"])] = f["fact_id"], b["value"]

    # -- fields --------------------------------------------------------------
    def field(self, subject, field, default=None):
        got = self._fields.get((subject, field))
        return got[1] if got else default

    def field_assertion(self, subject, field):
        """The assertion_id currently authoritative for (subject, field) — what
        citations/verifications target (ADR-0038: evidence points at assertions)."""
        got = self._fields.get((subject, field))
        return got[0] if got else None

    # -- identities ----------------------------------------------------------
    def node(self, node_id):
        n = self._nodes.get(node_id)
        if n is None:
            return None
        # category is CORRECTABLE (reclassify verb): a later field assertion wins
        # over the create-body value (the create body is just the initial claim).
        cat = self.field(node_id, "category")
        return {**n, "category": cat} if cat else n

    def edge(self, edge_id):
        return self._edges.get(edge_id)

    def nodes(self):
        return list(self._nodes)

    def resolve_redirect(self, node_id, _allow_missing=False):
        """Follow migrated_to to fixpoint; cycle → breaker (H4)."""
        seen = set()
        cur = node_id
        while True:
            if cur in seen:
                raise BreakerViolation(f"B4: redirect cycle at {cur}")
            seen.add(cur)
            nxt = self.field(cur, "migrated_to")
            if not nxt:
                return cur
            cur = nxt

    # -- edge queries (direction: provider -> consumer; both ways navigable) --
    def edges_in(self, node_id, types=None):
        """Edges whose CONSUMER is node_id (its requirements)."""
        return [e for e in self._edges.values()
                if e["to"] == node_id and (types is None or e["type"] in types)]

    def edges_out(self, node_id, types=None):
        """Edges whose PROVIDER is node_id (what it enables/joins)."""
        return [e for e in self._edges.values()
                if e["from"] == node_id and (types is None or e["type"] in types)]

    def taxonomy_parents(self, node_id):
        """IS_TYPE_OF / IS_REFINEMENT_OF flow child -> parent (RAM -> Memory)."""
        return [e["to"] for e in self.edges_out(node_id, TAXONOMY_TYPES)]

    def shadowed_by(self, edge_id):
        return self.field(edge_id, "shadowed_by", []) or []

    def is_shadowed(self, edge_id):
        return bool(self.shadowed_by(edge_id))
