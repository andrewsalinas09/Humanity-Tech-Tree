"""Seed the first taste of the iPhone corridor — through the REAL verb pipeline,
with real identities, so the viewer shows the trust language honestly:
some nodes vouched and cited (solid, no ring), most red and hollow (build from zero).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from httkdb.factlog import PgFactLog
from httkserver.service import Service

MIG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "migrations")

pg = PgFactLog()
pg.migrate(os.path.join(MIG, "001_init.sql"))
pg.migrate(os.path.join(MIG, "002_server.sql"))
pg.wipe()
with pg.conn.cursor() as c:
    c.execute("TRUNCATE identities, decision_tickets, search_receipts "
              "RESTART IDENTITY CASCADE")
pg.conn.commit()

svc = Service(pg)
svc.create_identity("tok-andrew", {"type": "human", "id": "andrew"})
svc.create_identity("tok-seed", {"type": "agent", "id": "seed-corridor-1",
                                 "model": "claude-fable-5"})


def agent_node(name, category, node_id=None):
    r = svc.search_similar("tok-seed", name)
    out = svc.propose_node("tok-seed", name, category=category,
                           search_receipt=r["receipt"], node_id=node_id)
    assert "applied" in out, out
    return node_id or name.lower().replace(" ", "-")


def verb(who, name, **params):
    out = svc.execute(f"tok-{who}", name, params)
    assert "applied" in out, (name, out)
    return out


# --- the agent floods the skeleton (all red, all hollow: build from zero) -----
silicon = agent_node("Silicon", "MATERIAL")
transistor = agent_node("Transistor", "TECHNOLOGY")
gate = agent_node("Logic Gate", "TECHNOLOGY", node_id="logic-gate")
tube = agent_node("Vacuum Tube", "TECHNOLOGY", node_id="vacuum-tube")
cpu = agent_node("CPU", "TECHNOLOGY")
iphone = agent_node("iPhone", "TECHNOLOGY")
liion = agent_node("Li-ion Battery", "TECHNOLOGY", node_id="li-ion-battery")
lithium = agent_node("Lithium", "MATERIAL")
em = agent_node("Electromagnetism", "NATURAL_LAW", node_id="electromagnetism")

verb("seed", "add_ingredient", product=transistor, ingredient=silicon,
     edge_id="e_si_tr")
verb("seed", "set_constraint", edge_id="e_si_tr", attr="purity", op="GT",
     value=0.99999, class_="PHYSICAL",
     citation="Sze & Ng, Physics of Semiconductor Devices, 3rd ed.")
verb("seed", "add_component", whole=gate, part=transistor, edge_id="e_tr_g")
verb("seed", "add_component", whole=gate, part=tube, edge_id="e_tu_g",
     role={"alternative": "e_tr_g"})
verb("seed", "set_constraint", edge_id="e_tu_g", attr="power_per_gate", op="LT",
     value=0.001)                                # FITNESS: ENIAC lived; iPhones can't
verb("seed", "set_attribute", node_id=tube, attr="power_per_gate", value=2.0)
verb("seed", "set_attribute", node_id=transistor, attr="power_per_gate", value=1e-7)
verb("seed", "set_attribute", node_id=silicon, attr="purity", value=0.999999)
verb("seed", "add_component", whole=cpu, part=gate)
verb("seed", "add_component", whole=iphone, part=cpu)
verb("seed", "add_component", whole=iphone, part=liion)
verb("seed", "add_ingredient", product=liion, ingredient=lithium)
verb("seed", "add_enabler", enabled=transistor, enabler=em)

# --- Andrew vouches for the foundations (standing EARNED, by name) ------------
for n in (silicon, lithium, em, transistor, tube, gate):
    verb("andrew", "correct", subject=n, fld="validity",
         new_value="current_truth", justification="verified: exists, well-documented")

print("seeded. solve(iphone):", svc.solve("tok-andrew", iphone))
print("solve(logic-gate):", svc.solve("tok-andrew", gate))
