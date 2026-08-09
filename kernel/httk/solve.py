"""Two-axis three-valued realizability over requirement expressions.

Implements: ADR-0017 expressions (+H11 vacuity, H12 shadow exemption, H13 claim
equivalence), ADR-0019/H17 taxonomy inheritance with EXCLUDE overrides across a DAG,
ADR-0037 Kleene evaluation, ADR-0039 PHYSICAL/FITNESS constraint classes (two axes),
ADR-0006 OPTIMIZES existence-skip, ADR-0025 possibility masks (works/people),
TB-041 hypothetical-leaf guard, TB-066 undeclared-attribute -> UNKNOWN,
TB-067 constraints-ride-the-claim, H3 regional availability, B1 hard-cycle detection,
TB-042 contradiction detector.

Expressions are tuples: ("edge", edge_id) | ("and", *children) | ("or", *children)
| ("not", child). Leaves reference EDGE IDENTITIES (ADR-0038 invariant).
"""
from dataclasses import dataclass, field
from .tri import Tri, t_and, t_or, t_not, RANK
from .store import HARD_TYPES, BreakerViolation
from .dates import Interval, point_in_span

MASKED_CATEGORIES = {"WORK_PUBLICATION", "BIOLOGICAL_ENTITY"}  # ADR-0025


@dataclass
class Result:
    existence: Tri
    fitness: Tri
    gaps: list = field(default_factory=list)     # (subject, why) for every UNKNOWN
    unfit: list = field(default_factory=list)    # (edge_id, constraint) for FITNESS VIOLs
    def pair(self):
        return (self.existence, self.fitness)


# -- effective requirement expression (own + implicit-AND + inherited) --------

def _claim_key(e):
    return (e["from"], e["to"], e["type"], e.get("qualifier"))


def _referenced_edges(expr, acc):
    if expr is None:
        return
    if expr[0] == "edge":
        acc.add(expr[1])
    else:
        for c in expr[1:]:
            _referenced_edges(c, acc)


def effective_expr(view, node_id, _seen=None):
    """Own expr AND implicit-AND of unreferenced hard edges (minus shadowed [H12],
    minus claim-duplicates [H13]) AND each taxonomy parent's effective expr (H17),
    with this node's EXCLUDE overrides pruning inherited leaves to vacuity (H11)."""
    _seen = _seen or frozenset()
    if node_id in _seen:
        return None  # taxonomy cycle guard; B1 catches dependency cycles separately
    own = view.field(node_id, "requirement_expr")

    referenced = set()
    _referenced_edges(own, referenced)
    referenced_claims = {(_claim_key(view.edge(e))) for e in referenced if view.edge(e)}

    implicit, seen_claims = [], set(referenced_claims)
    for e in view.edges_in(node_id, HARD_TYPES):
        if e["edge_id"] in referenced:
            continue
        if view.is_shadowed(e["edge_id"]):        # H12: shadowed exempt from implicit-AND
            continue
        ck = _claim_key(e)
        if ck in seen_claims:                      # H13: claim-equivalence dedupe
            continue
        seen_claims.add(ck)
        implicit.append(("edge", e["edge_id"]))

    parts = [p for p in [own, *implicit] if p is not None]

    excludes = set(view.field(node_id, "excludes", []) or [])  # ADR-0019 EXCLUDE
    for parent in view.taxonomy_parents(node_id):
        pex = effective_expr(view, parent, _seen | {node_id})
        pex = _prune_excluded(pex, excludes)       # H11: excluded leaves vacuous
        if pex is not None:
            parts.append(pex)

    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return ("and", *parts)


def _prune_excluded(expr, excludes):
    if expr is None:
        return None
    if expr[0] == "edge":
        return None if expr[1] in excludes else expr
    kids = [_prune_excluded(c, excludes) for c in expr[1:]]
    kids = [k for k in kids if k is not None]
    if not kids:
        return None                                # H11: all-pruned connective is vacuous
    if expr[0] == "not":
        return ("not", kids[0])
    if len(kids) == 1 and expr[0] in ("and", "or"):
        return kids[0]
    return (expr[0], *kids)


# -- constraint evaluation (ADR-0039 two classes; TB-066 UNKNOWN) --------------

def _check_constraints(view, edge, gaps, unfit):
    """Returns (existence_tri, fitness_tri) from this edge's constraints, evaluated
    against the edge's own provider (TB-067: constraints ride the claim)."""
    ex, fit = [Tri.SAT], [Tri.SAT]
    for c in view.field(edge["edge_id"], "constraints", []) or []:
        val = view.field(edge["from"], f"attrs.{c['attr']}")
        if val is None:
            (gaps).append((edge["edge_id"], f"attribute '{c['attr']}' undeclared on {edge['from']}"))
            tri = Tri.UNKNOWN                       # TB-066: never a silent pass
        else:
            ok = {"GT": val > c["value"], "LT": val < c["value"],
                  "EQ": val == c["value"]}[c["op"]]
            tri = Tri.SAT if ok else Tri.VIOL
        if c.get("class", "FITNESS") == "PHYSICAL":  # FITNESS is the default (ADR-0039)
            ex.append(tri)
        else:
            fit.append(tri)
            if tri is Tri.VIOL:
                unfit.append((edge["edge_id"], c))
    return t_and(ex), t_and(fit)


# -- the solve ----------------------------------------------------------------

def realizable(view, node_id, world_time=None, region=None, _stack=frozenset()):
    """Two-axis realizability of node_id at (world_time, region), possibility mode."""
    node_id = view.resolve_redirect(node_id)
    node = view.node(node_id)
    gaps, unfit = [], []
    if node is None:
        return Result(Tri.UNKNOWN, Tri.UNKNOWN, [(node_id, "stub: node unknown")], [])
    if node_id in _stack:
        # A hard dependency cycle reached us (B1 should have caught it at apply).
        return Result(Tri.UNKNOWN, Tri.SAT, [(node_id, "dependency cycle")], [])

    validity = view.field(node_id, "validity", "current_truth")
    if validity == "disproven":
        return Result(Tri.VIOL, Tri.SAT, [], [])

    expr = effective_expr(view, node_id)

    if expr is not None:
        ex, fit_expr, gaps, unfit = _eval(view, expr, world_time, region,
                                          _stack | {node_id})
        if ex is None:                              # whole expression vacuous (H11/masks)
            expr = None
        else:
            if validity == "hypothetical" and ex is Tri.SAT:
                ex = Tri.UNKNOWN                    # TB-041 cap
                gaps.append((node_id, "hypothetical: not realized even with deps met"))
            return Result(ex, fit_expr if fit_expr is not None else Tri.SAT, gaps, unfit)

    # Magic-box leaf (graceful ignorance) — but TB-041: hypothetical validity
    # blocks realization regardless of parents (no false unlocks).
    if validity == "hypothetical":
        return Result(Tri.UNKNOWN, Tri.SAT, [(node_id, "hypothetical, no realization")], [])
    return Result(Tri.SAT, Tri.SAT, gaps, unfit)


def _eval(view, expr, world_time, region, _stack):
    """Evaluate an expression → (existence, fitness, gaps, unfit).
    existence=None marks a VACUOUS subtree (H11 / ADR-0025 masks) — removed, not valued."""
    if expr[0] == "edge":
        return _eval_leaf(view, expr[1], world_time, region, _stack)
    if expr[0] == "not":
        ex, fit, g, u = _eval(view, expr[1], world_time, region, _stack)
        return t_not(ex), fit, g, u
    kids = [_eval(view, c, world_time, region, _stack) for c in expr[1:]]
    kids = [k for k in kids if k[0] is not None]          # drop vacuous children
    if not kids:
        return None, None, [], []                          # all-vacuous connective (H11)
    if expr[0] == "and":
        return (t_and(k[0] for k in kids), t_and(k[1] for k in kids),
                sum((k[2] for k in kids), []), sum((k[3] for k in kids), []))
    # OR: pick the best branch by (existence, fitness) — no cross-branch chimeras
    best = max(kids, key=lambda k: (RANK[k[0]], RANK[k[1]]))
    return best


def _eval_leaf(view, edge_id, world_time, region, _stack):
    edge = view.edge(edge_id)
    gaps, unfit = [], []
    if edge is None:
        return Tri.UNKNOWN, Tri.SAT, [(edge_id, "stub: edge unknown")], []

    provider = view.node(edge["from"])
    if provider and provider.get("category") in MASKED_CATEGORIES:
        # ADR-0025: possibility never gated by works/people — leaf is VACUOUS
        # (removed from composition; a masked leaf must not win an OR either).
        return None, None, [], []

    if view.is_shadowed(edge_id):
        # H12: satisfied by the edge OR any covering edge; constraints still this
        # edge's own, against its own provider (TB-067).
        covers = [_eval_leaf(view, c, world_time, region, _stack)
                  for c in view.shadowed_by(edge_id)]
        best = max(covers, key=lambda k: (RANK[k[0]], RANK[k[1]])) if covers else None
        cex, cfit, g2, u2 = best if best else (Tri.UNKNOWN, Tri.SAT, [], [])
        kex, kfit = _check_constraints(view, edge, gaps, unfit)
        return t_and([cex, kex]), t_and([cfit, kfit]), gaps + g2, unfit + u2

    # temporal gate (H2/ADR-0037): certain violation only; overlap folds in as UNKNOWN
    temporal = Tri.SAT
    if world_time is not None:
        start = view.field(edge_id, "start_date")
        end = view.field(edge_id, "end_date")
        temporal = point_in_span(world_time,
                                 Interval(**start) if start else None,
                                 Interval(**end) if end else None)
        if temporal is Tri.VIOL:
            return Tri.VIOL, Tri.SAT, [], []
        if temporal is Tri.UNKNOWN:
            gaps.append((edge_id, "date overlap: temporal status uncertain"))

    sub = realizable(view, edge["from"], world_time, region, _stack)
    kex, kfit = _check_constraints(view, edge, gaps, unfit)
    ex = t_and([sub.existence, kex, temporal])
    fit = t_and([sub.fitness, kfit])
    return ex, fit, gaps + sub.gaps, unfit + sub.unfit


# -- regional availability (H3: existential composition) ----------------------

def available(view, node_id, region, year):
    """ACTIVE covering → SAT; LOST covering with no ACTIVE → VIOL; no data → UNKNOWN.
    ACTIVE/LOST overlap → SAT + region-decomposition flag (H3/TB-049)."""
    tl = view.field(node_id, f"timeline.{region}")
    if tl is None:
        return Tri.UNKNOWN, []
    active = any(s["status"] == "ACTIVE" and s["start"] <= year <= s.get("end", 1e9)
                 for s in tl)
    lost = any(s["status"] == "LOST" and s["start"] <= year <= s.get("end", 1e9)
               for s in tl)
    if active and lost:
        return Tri.SAT, [f"region-decomposition bounty: {region} has ACTIVE/LOST overlap"]
    if active:
        return Tri.SAT, []
    if lost:
        return Tri.VIOL, []
    return Tri.UNKNOWN, []


# -- breakers & detectors ------------------------------------------------------

def find_hard_cycles(view):
    """B1: dependency cycles through hard edges only (OPTIMIZES legal — ADR-0006)."""
    graph = {}
    for n in view.nodes():
        graph[n] = [e["from"] for e in view.edges_in(n, HARD_TYPES)]
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    cycles = []

    def dfs(n, path):
        color[n] = GRAY
        for m in graph.get(n, []):
            if color.get(m, WHITE) == GRAY:
                cycles.append(path[path.index(m):] + [m] if m in path else [n, m])
            elif color.get(m, WHITE) == WHITE:
                dfs(m, path + [m])
        color[n] = BLACK

    for n in graph:
        if color[n] == WHITE:
            dfs(n, [n])
    return cycles


def contradictions(view):
    """TB-042: validity=current_truth (a cited fact: it exists) but existence VIOL
    (the graph can prove no support) — a missing-node bounty, never a paradox."""
    out = []
    for n in view.nodes():
        if view.field(n, "validity", "current_truth") == "current_truth":
            r = realizable(view, n)
            if r.existence is Tri.VIOL:
                out.append((n, "proven-true but no valid support path: missing nodes"))
    return out
