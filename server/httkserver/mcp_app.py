"""The two MCP faces over one Service (ADR-0041 §1).

stdio (attach your local Claude Code):
    python -m httkserver.mcp_app --token YOURTOKEN
HTTP (deployable; others attach theirs):
    python -m httkserver.mcp_app --http --port 8747
In HTTP mode the credential rides the Authorization header per call; in stdio
mode the launcher pins one credential for the session. Either way the SERVER
stamps identity — callers are never trusted (ADR-0041 §2).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "backend"))

from mcp.server.mcpserver import MCPServer      # noqa: E402  (MCP SDK 2.0)
from httkdb.factlog import PgFactLog            # noqa: E402
from httkserver.service import Service          # noqa: E402


def build_app(token_getter):
    svc = Service(PgFactLog())
    app = MCPServer("humanity-tech-tree",
                    instructions="Edit the Humanity Tech Tree via deterministic "
                                 "verbs (docs/VERBS.md). search_similar before "
                                 "propose_node; Decisions come back as tickets — "
                                 "resolve with resolve_decision.")

    @app.tool()
    def search_similar(query: str) -> dict:
        """Existence gate (mandatory before propose_node): find matching nodes, get a receipt."""
        return svc.search_similar(token_getter(), query)

    @app.tool()
    def propose_node(name: str, category: str = "TECHNOLOGY",
                     validity: str = "current_truth", search_receipt: int = None,
                     node_id: str = None) -> dict:
        """Create a node (requires a search_similar receipt; near-dupes open a ticket)."""
        return svc.propose_node(token_getter(), name, category, validity,
                                search_receipt, None, node_id)

    @app.tool()
    def verb(name: str, params: dict) -> dict:
        """Invoke any catalog verb (docs/VERBS.md) with keyword params.
        Returns applied | ticket (a Decision awaiting resolve_decision) | rejected."""
        return svc.execute(token_getter(), name, params)

    @app.tool()
    def resolve_decision(ticket_id: int, choice: dict, justification: str = None) -> dict:
        """Answer an open Decision ticket by picking one of its legal options."""
        return svc.resolve_decision(token_getter(), ticket_id, choice, justification)

    @app.tool()
    def open_tickets() -> list:
        """List open Decision tickets (the check queue)."""
        return svc.open_tickets(token_getter())

    @app.tool()
    def solve(node_id: str, world_time: float = None, region: str = None) -> dict:
        """Two-axis three-valued realizability with gap lists (ADR-0037/0039)."""
        return svc.solve(token_getter(), node_id, world_time, region)

    @app.tool()
    def get_node(node_id: str) -> dict:
        """A node's identity, fields, and edges both directions."""
        return svc.get_node(token_getter(), node_id)

    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("HTT_TOKEN"))
    ap.add_argument("--http", action="store_true")
    ap.add_argument("--port", type=int, default=8747)
    args = ap.parse_args()
    if not args.token and not args.http:
        raise SystemExit("stdio mode needs --token or HTT_TOKEN")
    app = build_app(lambda: args.token)
    if args.http:
        import anyio
        anyio.run(lambda: app.run_streamable_http_async(port=args.port))
    else:
        app.run()                                # stdio


if __name__ == "__main__":
    main()
