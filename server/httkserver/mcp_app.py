"""The two MCP faces over one Service (ADR-0041 §1).

stdio (attach your local Claude Code):
    python -m httkserver.mcp_app --token YOURTOKEN
HTTP (deployable; others attach theirs):
    python -m httkserver.mcp_app --http --port 8747
In HTTP mode the credential rides the Authorization header per call
(`Authorization: Bearer <token>`); in stdio mode the launcher pins one
credential for the session. When a header is present it ALWAYS wins — a
garbage header never falls back to the pinned token. Either way the SERVER
stamps identity — callers are never trusted (ADR-0041 §2).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "backend"))

from mcp.server.mcpserver import MCPServer, Context  # noqa: E402  (MCP SDK 2.0)
from httkdb.factlog import PgFactLog                 # noqa: E402
from httkserver.service import Service               # noqa: E402

_NO_CRED = {"rejected": {"rule": "AUTH",
                         "message": "no credential — send 'Authorization: "
                                    "Bearer <token>' (HTTP) or launch with "
                                    "--token (stdio)"}}


def _cred(ctx, pinned):
    """Per-call credential: Authorization header when present (and it always
    wins — garbage never falls back), else the stdio-pinned token."""
    headers = (ctx.headers if ctx is not None else None) or {}
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    if auth:                                   # malformed header ≠ fallback
        return auth.strip()
    return pinned


def build_app(pinned=None):
    svc = Service(PgFactLog())
    app = MCPServer("humanity-tech-tree",
                    instructions="Edit the Humanity Tech Tree via deterministic "
                                 "verbs (docs/VERBS.md). search_similar before "
                                 "propose_node; Decisions come back as tickets — "
                                 "resolve with resolve_decision. CITATIONS "
                                 "(ADR-0045): pass the doc-id/URL directly as "
                                 "source_node — NEVER create a node just to "
                                 "cite; work-nodes are only for story-"
                                 "significant works. Cite the claim being "
                                 "evidenced (dates, edges, constraints) — "
                                 "never the name.")

    @app.tool()
    def search_similar(query: str, ctx: Context) -> dict:
        """Existence gate (mandatory before propose_node): find matching nodes,
        get a receipt. Receipts are reusable but query-bound — search for the
        NAME you intend to propose, right before proposing it (a receipt for a
        different query proves nothing about your name's duplicates).
        Returns two lanes: 'matches' (exact/substring — these force duplicate
        tickets) and 'semantic' (nearest nodes by meaning, with descriptions
        and scores — YOU judge whether one already covers your concept; the
        receipt records what you were shown)."""
        tok = _cred(ctx, pinned)
        return svc.search_similar(tok, query) if tok else _NO_CRED

    @app.tool()
    def list_nodes(ctx: Context, category: str = None) -> list:
        """Browse all nodes (optionally by category) — for orienting before
        building, when search alone isn't enough."""
        tok = _cred(ctx, pinned)
        return svc.list_nodes(tok, category) if tok else [_NO_CRED]

    @app.tool()
    def propose_node(name: str, ctx: Context, category: str = "TECHNOLOGY",
                     validity: str = "current_truth", search_receipt: int = None,
                     node_id: str = None, description: str = None) -> dict:
        """Create a node (requires a search_similar receipt; near-dupes open a
        ticket). Include a 2-3 sentence description — what it is and why it
        matters; it powers learning AND future semantic search.
        Valid categories: TECHNOLOGY, MATERIAL, METHOD_TECHNIQUE, NATURAL_LAW,
        NATURAL_PHENOMENON, FORMAL_CONCEPT, CAPABILITY, STANDARD_UNIT,
        WORK_PUBLICATION, LEGISLATION, HISTORICAL_EVENT, SOCIETAL_ERA,
        SOCIETAL_NEED, BELIEF_SYSTEM, BIOLOGICAL_ENTITY, ORGANIZATION,
        GEOPOLITICAL_ENTITY, BRAND."""
        tok = _cred(ctx, pinned)
        return svc.propose_node(tok, name, category, validity, search_receipt,
                                None, node_id, description) if tok else _NO_CRED

    @app.tool()
    def verb(name: str, params: dict, ctx: Context) -> dict:
        """Invoke any catalog verb (docs/VERBS.md) with keyword params.
        Returns applied | ticket (a Decision awaiting resolve_decision) | rejected."""
        tok = _cred(ctx, pinned)
        return svc.execute(tok, name, params) if tok else _NO_CRED

    @app.tool()
    def resolve_decision(ticket_id: int, choice: dict, ctx: Context,
                         justification: str = None) -> dict:
        """Answer an open Decision ticket by picking one of its legal options."""
        tok = _cred(ctx, pinned)
        return svc.resolve_decision(tok, ticket_id, choice,
                                    justification) if tok else _NO_CRED

    @app.tool()
    def open_tickets(ctx: Context) -> list:
        """List open Decision tickets (the check queue)."""
        tok = _cred(ctx, pinned)
        return svc.open_tickets(tok) if tok else [_NO_CRED]

    @app.tool()
    def solve(node_id: str, ctx: Context, world_time: float = None,
              region: str = None) -> dict:
        """Two-axis three-valued realizability with gap lists (ADR-0037/0039)."""
        tok = _cred(ctx, pinned)
        return svc.solve(tok, node_id, world_time, region) if tok else _NO_CRED

    @app.tool()
    def get_node(node_id: str, ctx: Context) -> dict:
        """A node's identity, fields (with assertion ids), and edges both directions."""
        tok = _cred(ctx, pinned)
        return svc.get_node(tok, node_id) if tok else _NO_CRED

    @app.tool()
    def verify_citation(assertion_id: str, verdict: str, ctx: Context,
                        model: str = None, note: str = None) -> dict:
        """L2→L3 machine verification (ADR-0032): you fetched/checked the
        source — does it support the claim? verdict: supported | unsupported |
        hallucinated. Standing verifications earn reputation; bad ones cost."""
        tok = _cred(ctx, pinned)
        return svc.verify_citation(tok, assertion_id, verdict, model,
                                   note) if tok else _NO_CRED

    @app.tool()
    def confirm_verification(assertion_id: str, verdict: str, ctx: Context,
                             note: str = None) -> dict:
        """L3→L4 HUMAN confirmation (rejected for agent credentials): a person
        confirms the source supports the claim. verdict: supported | unsupported."""
        tok = _cred(ctx, pinned)
        return svc.confirm_verification(tok, assertion_id, verdict,
                                        note) if tok else _NO_CRED

    @app.tool()
    def resolve_challenge(challenge_id: str, outcome: str, ctx: Context,
                          demoted: list = None, note: str = None) -> dict:
        """ADMIN: ratify a challenge (upheld | rejected). Upheld executes the
        pre-staged remedy verbs; `demoted` assertion ids feed reputation."""
        tok = _cred(ctx, pinned)
        return svc.resolve_challenge(tok, challenge_id, outcome, demoted,
                                     note) if tok else _NO_CRED

    @app.tool()
    def open_challenge(subject: str, grounds: str, ctx: Context,
                       remedy: list = None) -> dict:
        """Dispute something you believe is wrong (node/edge/assertion id).
        Optionally pre-stage the fix as remedy=[{verb, params}] — executed
        verbatim if the challenge is upheld. Votes advise; an admin ratifies."""
        tok = _cred(ctx, pinned)
        return svc.open_challenge(tok, subject, grounds, remedy) if tok else _NO_CRED

    @app.tool()
    def vote_challenge(challenge_id: str, support: bool, reason: str,
                       ctx: Context) -> dict:
        """Vote on a challenge WITH your reason (recorded forever). Weight =
        1 + reputation, and only vested voters (3+ verified claims) count."""
        tok = _cred(ctx, pinned)
        return svc.vote_challenge(tok, challenge_id, support,
                                  reason) if tok else _NO_CRED

    @app.tool()
    def list_challenges(ctx: Context) -> list:
        """Open and resolved challenges — the dispute docket."""
        tok = _cred(ctx, pinned)
        return svc.list_challenges(tok) if tok else [_NO_CRED]

    @app.tool()
    def challenge_tally(challenge_id: str, ctx: Context) -> dict:
        """Current weighted tally for a challenge (advisory to the admin)."""
        tok = _cred(ctx, pinned)
        return svc.challenge_tally(tok, challenge_id) if tok else _NO_CRED

    @app.tool()
    def request_deletion(subject_id: str, reason: str, ctx: Context) -> dict:
        """Mark a node OR edge for deletion (ADR-0047): created-in-error nodes,
        or correct-but-no-longer-useful edges (coarse links superseded by
        richer structure). Opens a ticket only an ADMIN can approve; approval
        tombstones it — the log keeps full history, the view hides it."""
        tok = _cred(ctx, pinned)
        return svc.request_deletion(tok, subject_id, reason) if tok else _NO_CRED

    @app.tool()
    def post_request(want: str, ctx: Context, subject_node: str = None,
                     wanted_name: str = None, wanted_description: str = None,
                     notes: str = None, offered_sources: list = None) -> dict:
        """Ask for graph work: WANT_NODE (something should exist),
        WANT_COVERAGE (an existing node's dependencies are incomplete),
        WANT_EVIDENCE (claims need citations). offered_sources are
        citations-in-waiting: [{source, locator}]."""
        tok = _cred(ctx, pinned)
        return svc.post_request(tok, want, subject_node, wanted_name,
                                wanted_description, notes,
                                offered_sources) if tok else _NO_CRED

    @app.tool()
    def list_requests(ctx: Context, status: str = "open") -> list:
        """The bounty queue, most-endorsed first (status: open|fulfilled|all)."""
        tok = _cred(ctx, pinned)
        return svc.list_requests(tok, status) if tok else [_NO_CRED]

    @app.tool()
    def endorse_request(request_id: int, ctx: Context) -> dict:
        """Upvote a request — agents work the most-wanted first."""
        tok = _cred(ctx, pinned)
        return svc.endorse_request(tok, request_id) if tok else _NO_CRED

    @app.tool()
    def fulfill_request(request_id: int, links: list, ctx: Context,
                        note: str = None) -> dict:
        """Close a request NOW, linking the node/edge/assertion ids that satisfy
        it. Earns karma (3 + endorsements). Anyone can re-open later."""
        tok = _cred(ctx, pinned)
        return svc.fulfill_request(tok, request_id, links, note) if tok else _NO_CRED

    @app.tool()
    def reopen_request(request_id: int, reason: str, ctx: Context) -> dict:
        """Re-open a fulfilled request that missed the mark (say why)."""
        tok = _cred(ctx, pinned)
        return svc.reopen_request(tok, request_id, reason) if tok else _NO_CRED

    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("HTT_TOKEN"))
    ap.add_argument("--http", action="store_true")
    ap.add_argument("--port", type=int, default=8747)
    args = ap.parse_args()
    if not args.token and not args.http:
        raise SystemExit("stdio mode needs --token or HTT_TOKEN")
    app = build_app(pinned=args.token)
    if args.http:
        import anyio
        anyio.run(lambda: app.run_streamable_http_async(port=args.port))
    else:
        app.run()                                # stdio


if __name__ == "__main__":
    main()
