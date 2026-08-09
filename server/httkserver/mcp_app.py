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
                                 "resolve with resolve_decision.")

    @app.tool()
    def search_similar(query: str, ctx: Context) -> dict:
        """Existence gate (mandatory before propose_node): find matching nodes, get a receipt."""
        tok = _cred(ctx, pinned)
        return svc.search_similar(tok, query) if tok else _NO_CRED

    @app.tool()
    def propose_node(name: str, ctx: Context, category: str = "TECHNOLOGY",
                     validity: str = "current_truth", search_receipt: int = None,
                     node_id: str = None, description: str = None) -> dict:
        """Create a node (requires a search_similar receipt; near-dupes open a
        ticket). Include a 2-3 sentence description — what it is and why it
        matters; it powers learning AND future semantic search."""
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
