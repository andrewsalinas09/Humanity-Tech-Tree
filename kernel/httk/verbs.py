"""Verb compilers (ADR-0040, docs/VERBS.md): deterministic (view, params) ->
StagedFacts | Decision | Rejection. The LLM is never in here — Decisions carry
the complete legal option set; callers only choose.
"""
from dataclasses import dataclass, field

from .store import Store, View

PEOPLE_ORGS = {"BIOLOGICAL_ENTITY", "ORGANIZATION"}
KNOWLEDGE = {"NATURAL_LAW", "FORMAL_CONCEPT", "METHOD_TECHNIQUE", "WORK_PUBLICATION"}


@dataclass
class StagedFacts:
    facts: list                      # [(kind, body)]
    notes: list = field(default_factory=list)   # linter warns (advisory, L*)

    def apply(self, store: Store):
        for kind, body in self.facts:
            if kind == "node.create":
                store.append("node.create", body)
            elif kind == "edge.create":
                store.append("edge.create", body)
            elif kind == "assert":
                store.assert_field(body["subject"], body["field"], body["value"])
            elif kind == "retract":
                store.retract(body["target"])
        return self


@dataclass
class Decision:
    verb: str
    reason: str
    options: list                    # [{key, ...evidence}] — the COMPLETE legal set
    evidence: dict = field(default_factory=dict)


@dataclass
class Rejection:
    rule: str
    message: str


# ---------------------------------------------------------------- helpers ----

def _ancestors(view, node_id, _seen=None):
    _seen = _seen or set()
    out = set()
    for p in view.taxonomy_parents(node_id):
        if p not in _seen:
            _seen.add(p)
            out.add(p)
            out |= _ancestors(view, p, _seen)
    return out


def _shares_ancestor(view, a, b):
    return bool((_ancestors(view, a) | {a}) & (_ancestors(view, b) | {b}))


def _edge_extras(edge_id, start=None, end=None, epistemic=None, justification=None):
    """Q1 (ADR-0042 §3): initial conditions compiled at birth — one atomic CR.
    Anything unstated starts at zero, honestly labeled (unassessed/undated/red)."""
    facts = []
    if start is not None:
        facts.append(("assert", {"subject": edge_id, "field": "start_date", "value": start}))
    if end is not None:
        facts.append(("assert", {"subject": edge_id, "field": "end_date", "value": end}))
    if epistemic is not None:
        facts.append(("assert", {"subject": edge_id, "field": "epistemic", "value": epistemic}))
    if justification is not None:
        facts.append(("assert", {"subject": edge_id, "field": "justification",
                                 "value": justification}))
    return facts


def _claim_exists(view, frm, to, etype):
    """User ruling: adding a link that already exists must SAY SO."""
    for e in view.edges_in(to, {etype}):
        if e["from"] == frm and not view.is_shadowed(e["edge_id"]):
            return e["edge_id"]
    return None


def _add_or_alternative(view, consumer, new_edge, role, extras=None):
    dup = _claim_exists(view, new_edge["from"], new_edge["to"], new_edge["type"])
    if dup:
        return Rejection("EXISTS", f"this link already exists as edge '{dup}' — "
                                   "nothing to add (cite or refine it instead)")
    """The L11 trigger: same-type edge into consumer whose provider shares a
    taxonomy ancestor with the new provider ⇒ role REQUIRED."""
    siblings = [e for e in view.edges_in(consumer, {new_edge["type"]})
                if not view.is_shadowed(e["edge_id"])
                and _shares_ancestor(view, e["from"], new_edge["from"])]
    if siblings and role is None:
        return Decision(
            "add_*", "same-role candidates exist: additional or alternative? (L11)",
            options=[{"key": "additional"},
                     *({"key": "alternative", "to": e["edge_id"]} for e in siblings)],
            evidence={"siblings": [e["edge_id"] for e in siblings]})
    facts = [("edge.create", new_edge)] + (extras or [])
    if isinstance(role, dict) and role.get("alternative"):
        other = role["alternative"]
        expr = view.field(consumer, "requirement_expr")
        if expr is None:
            expr = ["or", ["edge", other], ["edge", new_edge["edge_id"]]]
        else:
            expr = ["or", expr, ["edge", new_edge["edge_id"]]]
        facts.append(("assert", {"subject": consumer, "field": "requirement_expr",
                                 "value": expr}))
    return StagedFacts(facts)


def _cat(view, node_id):
    n = view.node(node_id)
    return n["category"] if n else None


# ------------------------------------------------------- role-named verbs ----

def add_component(view, whole, part, role=None, edge_id=None,
                 start=None, end=None, epistemic=None, justification=None):
    if _cat(view, part) in PEOPLE_ORGS:
        return Rejection("L5", f"{part} is a person/org — people are never parts")
    eid = edge_id or f"e_{part}_{whole}"
    e = {"edge_id": eid, "from": part, "to": whole,
         "type": "IS_COMPONENT_OF", "qualifier": None}
    return _add_or_alternative(view, whole, e, role,
                               _edge_extras(eid, start, end, epistemic, justification))


def add_ingredient(view, product, ingredient, role=None, edge_id=None,
                   start=None, end=None, epistemic=None, justification=None):
    if _cat(view, ingredient) in PEOPLE_ORGS:
        return Rejection("L5", f"{ingredient} is a person/org — never an ingredient")
    eid = edge_id or f"e_{ingredient}_{product}"
    e = {"edge_id": eid, "from": ingredient,
         "to": product, "type": "IS_INGREDIENT_OF", "qualifier": None}
    return _add_or_alternative(view, product, e, role,
                               _edge_extras(eid, start, end, epistemic, justification))


def add_enabler(view, enabled, enabler, justification=None, edge_id=None,
                start=None, end=None, epistemic=None):
    notes = []
    if _cat(view, enabler) == "WORK_PUBLICATION" and _cat(view, enabled) not in PEOPLE_ORGS:
        notes.append("L1: depend on the concept the work codifies, not the paper")
    if _cat(view, enabled) == "BIOLOGICAL_ENTITY" and _cat(view, enabler) not in KNOWLEDGE:
        return Rejection("L2", "people receive only knowledge ENABLES")
    if _cat(view, enabler) == "BIOLOGICAL_ENTITY":
        if not justification:
            return Rejection("L3", "direct person link: justification required "
                                   "(substitutability default is 99.9% no)")
        notes.append("L3: direct person link — review-flagged")
    dup = _claim_exists(view, enabler, enabled, "ENABLES")
    if dup:
        return Rejection("EXISTS", f"this link already exists as edge '{dup}'")
    eid = edge_id or f"e_{enabler}_{enabled}"
    e = {"edge_id": eid, "from": enabler, "to": enabled, "type": "ENABLES",
         "qualifier": None}
    return StagedFacts([("edge.create", e)]
                       + _edge_extras(eid, start, end, epistemic, justification), notes)


def refine(view, family, version, edge_id=None,
           start=None, end=None, epistemic=None, justification=None):
    """version IS_REFINEMENT_OF family — the flat star (ADR-0018)."""
    notes = []
    cf, cv = _cat(view, family), _cat(view, version)
    if cf and cv and cf != cv:
        return Rejection("L4", "IS_REFINEMENT_OF requires same category")
    if view.edges_out(family, {"IS_REFINEMENT_OF"}):
        notes.append("ADR-0018: family is itself a version — flat star wants the root")
    eid = edge_id or f"r_{version}_{family}"
    e = {"edge_id": eid, "from": version, "to": family,
         "type": "IS_REFINEMENT_OF", "qualifier": None}
    return StagedFacts([("edge.create", e)]
                       + _edge_extras(eid, start, end, epistemic, justification), notes)


def succeed(view, old, new, qualifier, edge_id=None,
            start=None, end=None, epistemic=None, justification=None):
    """old SUCCEEDS new (dated story: replaced/superseded/spun-off/rebranded...)."""
    eid = edge_id or f"s_{old}_{new}"
    e = {"edge_id": eid, "from": old, "to": new, "type": "SUCCEEDS",
         "qualifier": qualifier}
    return StagedFacts([("edge.create", e)]
                       + _edge_extras(eid, start, end, epistemic, justification))


def associate(view, a, b, qualifier, edge_id=None,
              start=None, end=None, epistemic=None, justification=None):
    """Ghost-layer story edge (solver-invisible by type)."""
    eid = edge_id or f"a_{a}_{b}"
    e = {"edge_id": eid, "from": a, "to": b, "type": "ASSOCIATION",
         "qualifier": qualifier}
    return StagedFacts([("edge.create", e)]
                       + _edge_extras(eid, start, end, epistemic, justification))


def classify(view, instance, type_, edge_id=None):
    if type_ in (_ancestors(view, instance) | {instance}):
        pass  # re-classification idempotent-ish; DAG check below is the guard
    if instance in _ancestors(view, type_) or instance == type_:
        return Rejection("B1", "classification would create a taxonomy cycle")
    e = {"edge_id": edge_id or f"t_{instance}_{type_}", "from": instance,
         "to": type_, "type": "IS_TYPE_OF", "qualifier": None}
    notes = []
    ci, ct = _cat(view, instance), _cat(view, type_)
    if ci and ct and ci != ct:
        notes.append("L4: cross-category IS_TYPE_OF — review lane (Q-14)")
    return StagedFacts([("edge.create", e)], notes)


# ------------------------------------------------------------- intercept -----

LEGAL_LEG_TYPES = {"IS_COMPONENT_OF", "IS_INGREDIENT_OF", "ENABLES"}


def intercept(view, edge_id, via, first_leg_type=None, second_leg_type=None):
    """TB-068 compiler: two edges + shadow (never archive). Leg types are a
    Decision if omitted; constraints trigger the TB-067 relocation Decision."""
    edge = view.edge(edge_id)
    if edge is None:
        return Rejection("E404", f"edge {edge_id} unknown")
    if first_leg_type is None or second_leg_type is None:
        combos = [{"key": f"{a}+{b}", "first": a, "second": b}
                  for a in LEGAL_LEG_TYPES for b in LEGAL_LEG_TYPES
                  if edge["type"] in (a, b) or edge["type"] == "ENABLES"]
        return Decision("intercept", "choose leg types (only legal pairs offered)",
                        options=combos, evidence={"original_type": edge["type"]})
    e1 = {"edge_id": f"{edge_id}_a", "from": edge["from"], "to": via,
          "type": first_leg_type, "qualifier": None}
    e2 = {"edge_id": f"{edge_id}_b", "from": via, "to": edge["to"],
          "type": second_leg_type, "qualifier": None}
    staged = StagedFacts([
        ("edge.create", e1), ("edge.create", e2),
        ("assert", {"subject": edge_id, "field": "shadowed_by",
                    "value": [e1["edge_id"], e2["edge_id"]]}),
    ])
    if view.field(edge_id, "constraints"):
        staged.notes.append("TB-067 decision pending: constraints stay enforced "
                            "through the chain; relocation options: "
                            f"[stay, {e1['edge_id']}, {e2['edge_id']}]")
    return staged


# ------------------------------------------------- exclude / widen (ADR-0019)

def exclude(view, instance, family_edge, justification):
    edge = view.edge(family_edge)
    if edge is None:
        return Rejection("E404", f"edge {family_edge} unknown")
    if edge["to"] not in _ancestors(view, instance):
        return Rejection("ADR-0019", f"{family_edge} is not inherited by {instance}")
    ex = list(view.field(instance, "excludes", []) or [])
    if family_edge not in ex:
        ex.append(family_edge)
    return StagedFacts([("assert", {"subject": instance, "field": "excludes",
                                    "value": ex})],
                       [f"exclusion justified: {justification}"])


def widen(view, instance, family_edge, provider, to_ancestor=None, justification=""):
    """Legal targets = common ancestors of (original target, exceptional provider)."""
    edge = view.edge(family_edge)
    if edge is None:
        return Rejection("E404", f"edge {family_edge} unknown")
    common = sorted((_ancestors(view, edge["from"]) | {edge["from"]})
                    & (_ancestors(view, provider) | {provider}))
    if not common:
        return Rejection("H17", "no common ancestor — widening cannot express this; "
                                "the exceptional provider is a different kind entirely")
    if to_ancestor is None:
        if len(common) == 1:
            to_ancestor = common[0]
        else:
            return Decision("widen", "several common ancestors — all truth-preserving; "
                                     "choice is editorial (H17/Q-14)",
                            options=[{"key": c} for c in common])
    if to_ancestor not in common:
        return Rejection("H17", f"{to_ancestor} is not a common ancestor {common}")
    ov = list(view.field(instance, "widenings", []) or [])
    ov.append({"family_edge": family_edge, "relaxed_to": to_ancestor,
               "justification": justification})
    return StagedFacts([("assert", {"subject": instance, "field": "widenings",
                                    "value": ov})])


# ---------------------------------------------------------- merge / unmerge --

def merge(view, src, dst, justification=""):
    seen, cur = set(), dst
    while cur:
        if cur == src or cur in seen:
            return Rejection("B4", f"redirect {src}->{dst} closes a cycle")
        seen.add(cur)
        cur = view.field(cur, "migrated_to")
    aliases = sorted(set((view.field(src, "aliases", []) or [])
                         + (view.field(dst, "aliases", []) or [])
                         + [src]))
    return StagedFacts([
        ("assert", {"subject": src, "field": "migrated_to", "value": dst}),
        ("assert", {"subject": dst, "field": "aliases", "value": aliases}),
    ], [f"merge justified: {justification}"])


def unmerge(store, view, node, justification=""):
    """H5: forward-edit reopen + computed triage. Pre-merge assertion homes are
    COMPUTED (H5a) — only post-merge assertions become Decisions."""
    merge_seq = None
    for f in store.facts:
        b = f["body"]
        if (f["kind"] == "assert" and b.get("subject") == node
                and b.get("field") == "migrated_to" and b.get("value")):
            merge_seq = f["recorded_at"]
            target = b["value"]
    if merge_seq is None:
        return Rejection("H5", f"{node} is not merged")
    MERGE_BOOKKEEPING = {"aliases", "name_history"}   # mechanical unions (H6), not content
    post = [f["fact_id"] for f in store.facts
            if f["recorded_at"] > merge_seq and f["kind"] == "assert"
            and f["body"].get("subject") == target
            and f["body"].get("field") not in MERGE_BOOKKEEPING]
    staged = StagedFacts([("assert", {"subject": node, "field": "migrated_to",
                                      "value": None})],
                         [f"unmerge justified: {justification}"])
    triage = [Decision("unmerge", f"post-merge assertion {fid}: keep/move/park",
                       options=[{"key": "keep"}, {"key": "move", "to": node},
                                {"key": "park"}])
              for fid in post]
    return staged, triage


# ----------------------------------------------------------- evidence verbs --

def attach_citation(view, assertion_id, source_node, locator=None, subject=None):
    """Citation fact + the ALWAYS-CONNECTED rule (user): a source is never an
    island — citing also lays an ASSOCIATION(documents) ghost edge from the
    source to the claim's subject node (when the source IS a node; plain
    doc-id strings are the ADR-0045 default). The target may be an ASSERTION
    id or an EDGE id — citing an edge evidences the dependency claim itself
    (user ruling 2026-08-09: recorded intent makes future merges and
    reassignments never have to guess why a link exists)."""
    e = view.edge(assertion_id)
    if e is not None and subject is None:
        subject = e["to"]                    # the consumer whose claim it is
    facts = [("assert", {"subject": assertion_id, "field": "citation",
                         "value": {"source": source_node, "locator": locator}})]
    if subject and view.node(subject) and view.node(source_node):
        if not _claim_exists(view, source_node, subject, "ASSOCIATION"):
            facts.append(("edge.create", {
                "edge_id": f"a_{source_node}_{subject}", "from": source_node,
                "to": subject, "type": "ASSOCIATION", "qualifier": "documents"}))
    return StagedFacts(facts)


def correct(view, subject, fld, new_value, justification=""):
    """Supersession under the SAME identity (ADR-0038): metadata polish only."""
    return StagedFacts([("assert", {"subject": subject, "field": fld,
                                    "value": new_value})],
                       [f"correction: {justification}"])


def set_constraint(view, edge_id, attr, op, value, class_="FITNESS", citation=None):
    if class_ == "PHYSICAL" and not citation:
        return Rejection("L13", "PHYSICAL constraint requires a citation — "
                                "impossibility carries the burden of proof (ADR-0039)")
    cons = list(view.field(edge_id, "constraints", []) or [])
    cons.append({"attr": attr, "op": op, "value": value, "class": class_})
    return StagedFacts([("assert", {"subject": edge_id, "field": "constraints",
                                    "value": cons})])


# ================= texture verbs (every schema field is authorable) ==========

def set_attribute(view, node_id, attr, value):
    """Declare a node's attribute value (ADR-0004). Name canonicalization is the
    Q-20 gate's job upstream; the compiler is mechanical."""
    return StagedFacts([("assert", {"subject": node_id,
                                    "field": f"attrs.{attr}", "value": value})])


def add_time_segment(view, node_id, region, segment):
    """Regional timeline segment {status, start, end?, reason?} (H3/TB-004).
    ACTIVE/LOST overlap is legal but flags a region-decomposition bounty."""
    key = f"timeline.{region}"
    tl = list(view.field(node_id, key, []) or [])
    tl.append(segment)
    notes = []
    for a in tl:
        for b in tl:
            if (a is not b and {a["status"], b["status"]} == {"ACTIVE", "LOST"}
                    and a["start"] <= b.get("end", 1e9)
                    and b["start"] <= a.get("end", 1e9)):
                notes.append(f"H3: ACTIVE/LOST overlap in {region} — "
                             "region-decomposition bounty")
    return StagedFacts([("assert", {"subject": node_id, "field": key, "value": tl})],
                       sorted(set(notes)))


def date_edge(view, edge_id, start=None, end=None):
    facts = []
    if start is not None:
        facts.append(("assert", {"subject": edge_id, "field": "start_date",
                                 "value": start}))
    if end is not None:
        facts.append(("assert", {"subject": edge_id, "field": "end_date",
                                 "value": end}))
    return StagedFacts(facts)


def add_iteration(view, family, record):
    """ProductIteration data record (ADR-0009): {name, year, key_feature, tech_ids?}."""
    recs = list(view.field(family, "iterations", []) or [])
    if any(r["name"] == record["name"] for r in recs):
        return Rejection("ADR-0009", f"iteration '{record['name']}' already recorded")
    recs.append(record)
    return StagedFacts([("assert", {"subject": family, "field": "iterations",
                                    "value": recs})])


def lift_iteration(view, family, record_name, node_id=None):
    """The ADR-0018 §4 lifting operation: record → version node + edges.
    A pure resolution increase — the record's claims become graph structure."""
    recs = list(view.field(family, "iterations", []) or [])
    hit = next((r for r in recs if r["name"] == record_name), None)
    if hit is None:
        return Rejection("ADR-0018", f"no iteration record '{record_name}' on {family}")
    fam = view.node(family)
    nid = node_id or record_name.lower().replace(" ", "-").replace(".", "-")
    facts = [
        ("node.create", {"node_id": nid,
                         "category": fam["category"] if fam else "TECHNOLOGY"}),
        ("assert", {"subject": nid, "field": "validity", "value": "current_truth"}),
        ("edge.create", {"edge_id": f"r_{nid}_{family}", "from": nid, "to": family,
                         "type": "IS_REFINEMENT_OF", "qualifier": None}),
    ]
    if hit.get("year") is not None:
        facts.append(("assert", {"subject": f"r_{nid}_{family}", "field": "start_date",
                                 "value": {"year": hit["year"], "unc": 0.5}}))
    for t in hit.get("tech_ids", []):
        facts.append(("edge.create", {"edge_id": f"e_{t}_{nid}", "from": t,
                                      "to": nid, "type": "IS_COMPONENT_OF",
                                      "qualifier": None}))
    remaining = [r for r in recs if r["name"] != record_name]
    facts.append(("assert", {"subject": family, "field": "iterations",
                             "value": remaining}))
    return StagedFacts(facts, [f"lifted '{record_name}' → node {nid} (record→edges, "
                               "monotone resolution increase)"])


def rename(view, node_id, new_name, year=None):
    """Rebrand (ADR-0022): dated name_history; old name survives as an alias."""
    old = view.field(node_id, "name")
    hist = list(view.field(node_id, "name_history", []) or [])
    if hist and "end" not in hist[-1] and year is not None:
        hist[-1] = {**hist[-1], "end": year}
    hist.append({"name": new_name, "start": year})
    aliases = sorted(set((view.field(node_id, "aliases", []) or [])
                         + ([old] if old else [])))
    return StagedFacts([
        ("assert", {"subject": node_id, "field": "name", "value": new_name}),
        ("assert", {"subject": node_id, "field": "name_history", "value": hist}),
        ("assert", {"subject": node_id, "field": "aliases", "value": aliases}),
    ])


def add_alias(view, node_id, alias):
    aliases = sorted(set((view.field(node_id, "aliases", []) or []) + [alias]))
    return StagedFacts([("assert", {"subject": node_id, "field": "aliases",
                                    "value": aliases})])


def reclassify(view, node_id, new_category, justification=""):
    """Category is a correctable claim, not frozen identity. Deterministic check:
    existing edges that would violate linters under the new category are flagged."""
    notes = [f"reclassify justified: {justification}"]
    if new_category in PEOPLE_ORGS:
        bad = [e["edge_id"] for e in view.edges_out(node_id,
               {"IS_COMPONENT_OF", "IS_INGREDIENT_OF"})]
        if bad:
            notes.append(f"L5 conflicts under new category — review: {bad}")
    return StagedFacts([("assert", {"subject": node_id, "field": "category",
                                    "value": new_category})], notes)


def retract_assertion(view, assertion_id, justification=""):
    """Spurious claim, no replacement: forward-fact retraction (ADR-0011)."""
    return StagedFacts([("retract", {"target": assertion_id})],
                       [f"retraction: {justification}"])


def mark_shadowed(view, edge_id, covering, confirmation=""):
    """Human-confirmed resolution of the L8 redundancy linter (ADR-0021/TB-025)."""
    if view.edge(edge_id) is None:
        return Rejection("E404", f"edge {edge_id} unknown")
    missing = [c for c in covering if view.edge(c) is None]
    if missing or not covering:
        return Rejection("ADR-0021", f"covering edges missing/empty: {missing}")
    return StagedFacts([("assert", {"subject": edge_id, "field": "shadowed_by",
                                    "value": list(covering)})],
                       [f"coverage human-confirmed (L8): {confirmation}"])


def add_alternative_bundle(view, consumer, alternative_to, parts):
    """TB-021's shape: an OR branch that is an AND of several new edges
    ('palladium + heat' as one option against 'platinum')."""
    alt = view.edge(alternative_to)
    if alt is None or alt["to"] != consumer:
        return Rejection("ADR-0017", f"{alternative_to} is not an edge into {consumer}")
    facts, leaf_ids = [], []
    for p in parts:
        if _cat(view, p["provider"]) in PEOPLE_ORGS and p["type"] != "ENABLES":
            return Rejection("L5", f"{p['provider']} is a person/org — never a part")
        eid = p.get("edge_id") or f"e_{p['provider']}_{consumer}"
        facts.append(("edge.create", {"edge_id": eid, "from": p["provider"],
                                      "to": consumer, "type": p["type"],
                                      "qualifier": None}))
        leaf_ids.append(eid)
    branch = (["edge", leaf_ids[0]] if len(leaf_ids) == 1
              else ["and", *(["edge", e] for e in leaf_ids)])
    expr = view.field(consumer, "requirement_expr")
    expr = (["or", ["edge", alternative_to], branch] if expr is None
            else ["or", expr, branch])
    facts.append(("assert", {"subject": consumer, "field": "requirement_expr",
                             "value": expr}))
    return StagedFacts(facts)


def move_assertion(store, view, assertion_id, new_subject, justification=""):
    """Un-merge triage resolution 'move': re-home a claim (new assert + retract old)."""
    src = next((f for f in store.facts
                if f["fact_id"] == assertion_id and f["kind"] == "assert"), None)
    if src is None:
        return Rejection("E404", f"assertion {assertion_id} unknown")
    b = src["body"]
    return StagedFacts([
        ("assert", {"subject": new_subject, "field": b["field"], "value": b["value"]}),
        ("retract", {"target": assertion_id}),
    ], [f"moved {b['field']} from {b['subject']} → {new_subject}: {justification}"])


def park_assertion(store, view, assertion_id, ancestor, justification=""):
    """Un-merge triage 'park' (H5c): re-home at a coarser-but-true ancestor,
    flagged as a bounty — never forced into a possibly-false home."""
    r = move_assertion(store, view, assertion_id, ancestor, justification)
    if isinstance(r, StagedFacts):
        flags = list(view.field(ancestor, "flags", []) or [])
        flags.append({"kind": "parked-claim", "assertion": assertion_id,
                      "note": justification})
        r.facts.append(("assert", {"subject": ancestor, "field": "flags",
                                   "value": flags}))
        r.notes.append("parked: resolution bounty open (H5c)")
    return r


def flag(view, subject, grounds):
    """The bounty entry point: mark anything as needing attention (README's
    original gameplay; ADR-0025 §6 absurd-trace diagnosis lands here too)."""
    flags = list(view.field(subject, "flags", []) or [])
    flags.append({"grounds": grounds})
    return StagedFacts([("assert", {"subject": subject, "field": "flags",
                                    "value": flags})])
