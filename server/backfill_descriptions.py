"""Backfill descriptions for every existing node (user ruling 2026-08-09:
description = what it is + why it matters; feeds learning AND the future
Q-20 semantic gate). Uses the `correct` verb — description is metadata."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from httkdb.factlog import PgFactLog
from httkserver.service import Service

D = {
 "electromagnetism": "The physics of electric and magnetic fields and their interplay, unified by Maxwell. Every radio wave, circuit, and antenna is an application of it.",
 "semiconductor-physics": "The band-structure physics explaining why materials like silicon conduct only under control — doping, junctions, carrier behavior. The scientific bedrock beneath every transistor.",
 "silicon": "The second-most abundant element in Earth's crust and the workhorse semiconductor. Refined to extreme purity, it becomes the substrate of nearly all modern chips.",
 "vacuum-tube": "A sealed glass tube controlling electron flow between electrodes — the first practical electronic amplifier and switch. It ran early radio, radar, and computers until the transistor displaced it.",
 "transistor": "A semiconductor device that amplifies or switches electrical signals (Bell Labs, 1947). The fundamental building block of all modern electronics — billions now sit in every phone.",
 "logic-gate": "A circuit implementing a Boolean operation (AND, OR, NOT) over voltage levels. Chained by the million, gates turn switching into computation.",
 "cpu": "The central processing unit: a chip that fetches, decodes, and executes instructions. The general-purpose engine of computing, built from logic gates.",
 "crystal-oscillator": "A quartz crystal that vibrates at a precise frequency when driven electrically, providing the clock signal that synchronizes digital circuits and radios.",
 "iphone": "Apple's 2007 smartphone that fused a phone, computer, camera, and touch interface into one slab — the consumer summit resting on nearly every branch of this tree.",
 "li-ion-battery": "A rechargeable battery moving lithium ions between electrodes (commercialized by Sony, 1991). Its energy density made portable electronics and EVs practical.",
 "lithium": "The lightest metal and most electropositive element. Its electrochemistry makes it the key ingredient of high-density rechargeable batteries.",
 "lithium-carbonate": "The standard industrial lithium feedstock (Li2CO3), refined from ore or brine, from which battery chemicals and lithium metal are produced.",
 "spodumene": "A hard-rock pyroxene mineral and the principal lithium ore, mined chiefly in Australia and roasted to extract lithium.",
 "lithium-brine": "Lithium-rich groundwater beneath salt flats (salars) in Chile, Argentina, and Bolivia — pumped to the surface as the other main lithium source.",
 "brine-evaporation": "Concentrating salar brine in vast solar ponds for 12-18 months until lithium salts can be precipitated — cheap, slow, land- and water-intensive.",
 "molten-salt-electrolysis": "Winning reactive metals by passing current through their molten salts. Lithium metal is produced from a molten LiCl-KCl bath this way.",
 "mining": "Extracting useful minerals from the earth — among humanity's oldest industries and the physical entry point of nearly every material supply chain.",
 "802-11": "The IEEE standard family for wireless local-area networking — WiFi. It turned the unlicensed ISM bands into the world's default way to reach the internet.",
 "802-11b": "The 1999 amendment that made WiFi mainstream: 11 Mbit/s in the 2.4 GHz band using spread-spectrum techniques, cheap enough for homes.",
 "802-11g": "The 2003 amendment bringing OFDM to 2.4 GHz for 54 Mbit/s while staying compatible with 802.11b hardware.",
 "802-11n": "The 2009 amendment (marketed as WiFi 4) that added MIMO — multiple antennas multiplying throughput past 100 Mbit/s.",
 "802-11ax": "The 2019 amendment (WiFi 6) using OFDMA to serve many devices efficiently in dense environments.",
 "spread-spectrum": "Transmitting a signal deliberately spread across a wide frequency band, trading bandwidth for resistance to interference and interception. Born military, now the basis of WiFi, GPS, and Bluetooth.",
 "csma-ca": "Carrier-sense multiple access with collision avoidance: the listen-before-talk etiquette that lets many radios share one channel without a coordinator.",
 "rf-transceiver": "The radio-frequency front end that turns digital bits into modulated radio waves and back — the physical voice and ears of every wireless device.",
 "ism-deregulation": "The FCC's 1985 decision permitting unlicensed spread-spectrum use in the ISM bands. This regulatory unlock, not a device, is what made WiFi legally possible.",
 "fft": "The fast Fourier transform: an algorithm computing frequency content in O(n log n) (Cooley-Tukey, 1965). It made real-time signal processing computationally feasible.",
 "ofdm": "Orthogonal frequency-division multiplexing: sending data over many overlapping-but-orthogonal subcarriers, computed via FFT. The modulation backbone of WiFi, LTE, and DSL.",
 "mimo": "Multiple-input multiple-output radio: using several antennas to send parallel data streams through the same spectrum, multiplying capacity without new bandwidth.",
 "ofdma": "OFDM extended to multiple access: subcarriers assigned to different users simultaneously, letting one channel efficiently serve many small transmissions.",
 "tsf": "The timing synchronization function keeping all stations in a WiFi network on a shared microsecond clock, so power-saving and frequency hopping stay coordinated.",
 "hedy-lamarr": "Hollywood actress and inventor who, with George Antheil, patented frequency-hopping spread spectrum in 1942 — a lineage that reaches today's wireless standards.",
 "us2292387": "The 1942 Markey/Antheil 'Secret Communication System' patent describing frequency hopping to protect torpedo guidance from jamming — the canonical spread-spectrum origin document.",
 "fcc-81-413": "The FCC rulemaking docket whose 1985 Report & Order authorized unlicensed spread-spectrum operation — the paper trail behind WiFi's legal existence.",
 "usgs-mcs": "The US Geological Survey's annual Mineral Commodity Summaries — the standard public reference for production, reserves, and uses of industrial minerals.",
 "semiconductor-physics-source": None,  # guard against typos; unused
}

svc = Service(PgFactLog())
_, view = svc._kernel()
nodes = sorted(view.nodes())
missing = [n for n in nodes if n not in D]
if missing:
    print("NO DESCRIPTION AUTHORED FOR:", missing)

done = skip = 0
for n in nodes:
    text = D.get(n)
    if not text:
        continue
    if view.field(n, "description"):
        skip += 1
        continue
    out = svc.execute("tok-andrew", "correct",
                      {"subject": n, "fld": "description", "new_value": text,
                       "justification": "description backfill (2026-08-09 ruling)"})
    assert "applied" in out, (n, out)
    done += 1
print(f"described {done} nodes ({skip} already had one); total {len(nodes)}")
