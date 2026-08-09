"""Stress the MCP surface for real (ADR-0041) while adding the lithium→mining
corridor — every write goes through the actual MCP protocol over HTTP, exactly
the way agent authors will. Reports PASS/FAIL per probe plus findings."""
import json

import anyio
import httpx

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://localhost:8747/mcp"
FINDINGS = []


def out(res):
    """CallToolResult → dict (structured if present, else parse text)."""
    if getattr(res, "structuredContent", None):
        sc = res.structuredContent
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    for c in res.content or []:
        if getattr(c, "text", None):
            try:
                return json.loads(c.text)
            except json.JSONDecodeError:
                return {"text": c.text}
    return {}


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))
    if not ok:
        FINDINGS.append(f"FAIL {label}: {detail}")


async def main():
    hc = httpx.AsyncClient(headers={"Authorization": "Bearer tok-andrew"})
    async with streamable_http_client(URL, http_client=hc) as (r, w, *_):
        async with ClientSession(r, w) as s:
            await s.initialize()

            # ---------- A. protocol + guardrail probes ----------------------
            tools = await s.list_tools()
            names = sorted(t.name for t in tools.tools)
            check("tools/list has the 7-verb surface", len(names) == 7, ",".join(names))

            res = out(await s.call_tool("search_similar", {"query": "lithium"}))
            check("existence gate returns receipt+match",
                  isinstance(res.get("receipt"), int)
                  and any(m["node_id"] == "lithium" for m in res["matches"]),
                  str(res.get("matches")))
            lithium_receipt = res.get("receipt")

            res = out(await s.call_tool("propose_node", {"name": "Lithium Mining"}))
            check("propose without receipt REJECTED (Q-20)",
                  res.get("rejected", {}).get("rule") == "Q-20")

            res = out(await s.call_tool("propose_node",
                                        {"name": "Lithium",
                                         "search_receipt": lithium_receipt}))
            tid = res.get("ticket")
            check("exact-dupe propose opens Decision ticket", tid is not None, str(res))
            if tid is not None:
                res = out(await s.call_tool("resolve_decision",
                                            {"ticket_id": tid,
                                             "choice": {"key": "use_existing",
                                                        "node_id": "lithium"}}))
                check("ticket resolves to use_existing",
                      res.get("applied", {}).get("existing") == "lithium", str(res))

            res = out(await s.call_tool("verb", {"name": "no_such_verb", "params": {}}))
            check("unknown verb rejected E404",
                  res.get("rejected", {}).get("rule") == "E404")

            # ---------- B. the corridor, through MCP only -------------------
            async def new_node(name, category, node_id):
                sr = out(await s.call_tool("search_similar", {"query": name}))
                if any(m["node_id"] == node_id for m in sr.get("matches", [])):
                    print(f"  = {node_id} already exists, reusing")
                    return
                res = out(await s.call_tool("propose_node",
                                            {"name": name, "category": category,
                                             "validity": "current_truth",
                                             "search_receipt": sr["receipt"],
                                             "node_id": node_id}))
                ok = "applied" in res
                check(f"node {node_id}", ok, "" if ok else str(res))

            async def verb(vname, **params):
                res = out(await s.call_tool("verb", {"name": vname, "params": params}))
                return res

            await new_node("Mining", "METHOD_TECHNIQUE", "mining")
            await new_node("Spodumene", "MATERIAL", "spodumene")
            await new_node("Lithium Brine", "MATERIAL", "lithium-brine")
            await new_node("Solar Brine Evaporation", "METHOD_TECHNIQUE",
                           "brine-evaporation")
            await new_node("Lithium Carbonate", "MATERIAL", "lithium-carbonate")
            await new_node("Molten-Salt Electrolysis", "METHOD_TECHNIQUE",
                           "molten-salt-electrolysis")
            await new_node("USGS Mineral Commodity Summaries", "WORK_PUBLICATION",
                           "usgs-mcs")

            edges = [
                ("add_enabler", dict(enabled="spodumene", enabler="mining",
                                     justification="ore reaches industry only through extraction")),
                ("add_ingredient", dict(product="lithium-carbonate",
                                        ingredient="spodumene")),
                ("add_ingredient", dict(product="lithium-carbonate",
                                        ingredient="lithium-brine")),
                ("add_enabler", dict(enabled="lithium-carbonate",
                                     enabler="brine-evaporation",
                                     justification="salar brines concentrate by solar evaporation")),
                ("add_ingredient", dict(product="lithium",
                                        ingredient="lithium-carbonate")),
                ("add_enabler", dict(enabled="lithium",
                                     enabler="molten-salt-electrolysis",
                                     justification="Li metal won by LiCl-KCl electrolysis")),
            ]
            for vname, params in edges:
                res = await verb(vname, **params)
                ok = ("applied" in res or "ticket" in res
                      or res.get("rejected", {}).get("rule") == "EXISTS")
                tag = "applied" if "applied" in res else str(res)
                check(f"{vname} {list(params.values())[0]}<-{list(params.values())[1]}",
                      ok, "" if ok else tag)
                if "ticket" in res:
                    print(f"   ticket opened: {res.get('reason')}")

            # duplicate-claim gate fires through MCP too
            res = await verb("add_ingredient", product="lithium-carbonate",
                             ingredient="spodumene")
            check("duplicate edge claim rejected EXISTS",
                  res.get("rejected", {}).get("rule") == "EXISTS", str(res)[:90])

            # ---------- C. citation via MCP (assertion ids now exposed) -----
            gn = out(await s.call_tool("get_node", {"node_id": "lithium-carbonate"}))
            aid = gn.get("fields", {}).get("name", {}).get("assertion")
            check("get_node exposes assertion ids", aid is not None, str(aid))
            if aid:
                res = await verb("attach_citation", assertion_id=aid,
                                 source_node="usgs-mcs",
                                 locator="USGS MCS 2024, Lithium, pp. 108-109")
                check("attach_citation through MCP", "applied" in res, str(res)[:120])

            # ---------- D. the solver sees the new chain --------------------
            res = out(await s.call_tool("solve", {"node_id": "li-ion-battery"}))
            check("solve(li-ion-battery) answers",
                  res.get("existence") in ("SATISFIED", "UNKNOWN", "VIOLATED"),
                  f"existence={res.get('existence')} gaps={len(res.get('gaps', []))}")
            res = out(await s.call_tool("solve", {"node_id": "lithium"}))
            print(f"   solve(lithium): existence={res.get('existence')}, "
                  f"gaps={res.get('gaps')}")

            tickets = out(await s.call_tool("open_tickets", {}))
            tl = tickets if isinstance(tickets, list) else tickets.get("result", tickets)
            print(f"   open tickets after run: {tl if tl else 'none'}")

    # ---------- E. header-auth probe (separate connection) ------------------
    for label, headers in (("bogus token", {"Authorization": "Bearer tok-BOGUS"}),
                           ("no header", {})):
        hc2 = httpx.AsyncClient(headers=headers)
        try:
            async with streamable_http_client(URL, http_client=hc2) as (r, w, *_):
                async with ClientSession(r, w) as s:
                    await s.initialize()
                    res = await s.call_tool("search_similar", {"query": "x"})
                    body = out(res)
                    if (getattr(res, "is_error", False)
                            or getattr(res, "isError", False)
                            or "rejected" in body):
                        print(f"PROBE header auth ({label}): rejected OK")
                    else:
                        FINDINGS.append(f"header auth: {label} ACCEPTED — "
                                        "ADR-0041 §2 violated")
                        print(f"PROBE header auth ({label}): ACCEPTED (finding)")
        except Exception as e:
            print(f"PROBE header auth ({label}): rejected at transport "
                  f"({type(e).__name__}) OK")

    print("\n=== FINDINGS ===")
    for f in FINDINGS or ["none — surface held"]:
        print("-", f)


anyio.run(main)
