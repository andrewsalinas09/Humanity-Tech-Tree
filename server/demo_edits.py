"""User-directed live edits: the duplicate gate, the intercept, the connected docket."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from httkdb.factlog import PgFactLog
from httkserver.service import Service

svc = Service(PgFactLog())

print("=== 1) CPU <- crystal oscillator ===")
r = svc.search_similar("tok-andrew", "crystal oscillator")
print("existence gate:", r["matches"], "-> node already exists; REUSING it")
out = svc.execute("tok-andrew", "add_component",
                  {"whole": "cpu", "part": "crystal-oscillator",
                   "justification": "CPU clock generation"})
print("first add:", out.get("applied", out))

out = svc.execute("tok-andrew", "add_component",
                  {"whole": "cpu", "part": "crystal-oscillator"})
print("second add:", out)                       # must SAY it already exists

print("\n=== 2) intercept: electromagnetism -> transistor is too coarse ===")
r = svc.search_similar("tok-andrew", "semiconductor physics")
out = svc.propose_node("tok-andrew", "Semiconductor Physics",
                       category="NATURAL_LAW", validity="current_truth",
                       search_receipt=r["receipt"], node_id="semiconductor-physics")
print("new node:", out.get("applied", out))
out = svc.execute("tok-andrew", "intercept",
                  {"edge_id": "e_electromagnetism_transistor",
                   "via": "semiconductor-physics"})
print("intercept without leg types -> ticket:", out.get("ticket"), out.get("reason"))
done = svc.resolve_decision("tok-andrew", out["ticket"],
                            {"key": "ENABLES+ENABLES",
                             "first": "ENABLES", "second": "ENABLES"})
print("resolved:", done.get("applied", done))

print("\n=== 3) the docket is never an island (always-connected rule) ===")
out = svc.execute("tok-andrew", "associate",
                  {"a": "fcc-81-413", "b": "ism-deregulation",
                   "qualifier": "documents"})
print("docket edge:", out.get("applied", out))

print("\nsolve(transistor):", svc.solve("tok-andrew", "transistor"))
