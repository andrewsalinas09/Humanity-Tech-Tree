"""The 802.11 worked example (docs/examples/802-11-worked-example.md) becomes
real facts — ADDITIVE (no wipe: order-independence means it just lands on the
existing corridor). Agent seeds; Andrew vouches the bedrock; versions stay red
for the game. Watch the map while this runs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from httkdb.factlog import PgFactLog
from httkserver.service import Service

svc = Service(PgFactLog())


def node(name, category, node_id=None, who="seed"):
    r = svc.search_similar(f"tok-{who}", name)
    out = svc.propose_node(f"tok-{who}", name, category=category,
                           search_receipt=r["receipt"], node_id=node_id)
    assert "applied" in out, (name, out)
    return node_id or name.lower().replace(" ", "-")


def verb(who, vname, **params):
    out = svc.execute(f"tok-{who}", vname, params)
    assert "applied" in out, (vname, out)
    return out


Y = lambda y, u=0.5: {"year": float(y), "unc": u}

# --- the family root and its family-wide truths -------------------------------
wifi = node("802.11 Wireless LAN", "STANDARD_UNIT", node_id="802-11")
for a in ("WiFi", "Wi-Fi", "WLAN"):
    verb("seed", "add_alias", node_id=wifi, alias=a)

spread = node("Spread Spectrum", "METHOD_TECHNIQUE", node_id="spread-spectrum")
csma = node("CSMA/CA", "METHOD_TECHNIQUE", node_id="csma-ca")
ism = node("ISM Band Deregulation (FCC 1985)", "LEGISLATION", node_id="ism-deregulation")
rf = node("RF Transceiver", "TECHNOLOGY", node_id="rf-transceiver")
xtal = node("Crystal Oscillator", "TECHNOLOGY", node_id="crystal-oscillator")
tsf = node("Timing Synchronization Function", "METHOD_TECHNIQUE", node_id="tsf")

verb("seed", "add_enabler", enabled=wifi, enabler=spread, start=Y(1997))
verb("seed", "add_enabler", enabled=wifi, enabler=ism, start=Y(1997),
     justification="no unlicensed spectrum, no WiFi")
verb("seed", "add_component", whole=wifi, part=csma, start=Y(1997))
verb("seed", "add_component", whole=wifi, part=rf)
verb("seed", "add_component", whole=wifi, part=xtal,
     justification="microsecond MAC timing")
verb("seed", "add_component", whole=wifi, part=tsf, start=Y(1997),
     justification="TSF is family-wide since the 1997 base MAC")
verb("seed", "add_component", whole=tsf, part=xtal)

# --- the human layer (ghost edges — hidden until History Mode) ----------------
lamarr = node("Hedy Lamarr", "BIOLOGICAL_ENTITY", node_id="hedy-lamarr")
patent = node("Secret Communication System (US2292387)", "WORK_PUBLICATION",
              node_id="us2292387")
verb("seed", "associate", a=lamarr, b=patent, qualifier="authored", start=Y(1942))
verb("seed", "associate", a=patent, b=spread, qualifier="codifies")

# --- significance-gated version nodes with their earning dependencies ---------
ofdm = node("OFDM", "METHOD_TECHNIQUE", node_id="ofdm")
fft = node("Fast Fourier Transform", "FORMAL_CONCEPT", node_id="fft")
mimo = node("MIMO", "METHOD_TECHNIQUE", node_id="mimo")
ofdma = node("OFDMA", "METHOD_TECHNIQUE", node_id="ofdma")
verb("seed", "add_enabler", enabled=ofdm, enabler=fft)

b = node("802.11b", "STANDARD_UNIT", node_id="802-11b")
g = node("802.11g", "STANDARD_UNIT", node_id="802-11g")
n11 = node("802.11n", "STANDARD_UNIT", node_id="802-11n")
ax = node("802.11ax", "STANDARD_UNIT", node_id="802-11ax")
verb("seed", "add_alias", node_id=n11, alias="WiFi 4")
verb("seed", "add_alias", node_id=ax, alias="WiFi 6")

for v, yr in ((b, 1999), (g, 2003), (n11, 2009), (ax, 2019)):
    verb("seed", "refine", family=wifi, version=v, start=Y(yr))
verb("seed", "add_enabler", enabled=g, enabler=ofdm)
verb("seed", "add_enabler", enabled=n11, enabler=mimo)
verb("seed", "add_enabler", enabled=ax, enabler=ofdma)

# the story wave (ghost layer): each replaced by the next
verb("seed", "succeed", old=b, new=g, qualifier="replaced", start=Y(2003))
verb("seed", "succeed", old=g, new=n11, qualifier="replaced", start=Y(2009))
verb("seed", "succeed", old=n11, new=ax, qualifier="replaced", start=Y(2019))

# a version that FAILS the significance filter → iteration record (ADR-0009)
verb("seed", "add_iteration", family=wifi,
     record={"name": "802.11j", "year": 2004, "key_feature": "Japan 4.9/5.0 GHz"})

# --- the corridor joins the iPhone -------------------------------------------
verb("seed", "add_enabler", enabled="iphone", enabler=wifi, start=Y(2007),
     justification="coarse family link; refine to versions later (ADR-0018)")

# --- Andrew vouches the bedrock; versions stay red for the game ---------------
for nid in (wifi, spread, csma, ism, rf, xtal, tsf, fft, ofdm, b, g):
    verb("andrew", "correct", subject=nid, fld="validity",
         new_value="current_truth", justification="verified, well-documented")

# --- the first real citation: page-and-docket precision (ADR-0030/0038) -------
fcc = node("FCC Report & Order, Docket 81-413", "WORK_PUBLICATION",
           node_id="fcc-81-413", who="andrew")
view_aid = None
with svc.pg.conn.cursor() as c:
    c.execute("SELECT assertion_fact_id FROM current_fields "
              "WHERE subject_id=%s AND field_path='validity'", (ism,))
    view_aid = c.fetchone()[0]
verb("andrew", "attach_citation", assertion_id=view_aid, source_node=fcc,
     locator="47 CFR 15.247, adopted May 9, 1985")

print("WiFi corridor landed.")
print("solve(802-11):", svc.solve("tok-andrew", wifi))
print("solve(iphone):", svc.solve("tok-andrew", "iphone"))
