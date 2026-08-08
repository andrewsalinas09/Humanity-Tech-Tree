# Worked example: the 802.11 family

The validation exercise for the version-family pattern (Q-18 → ADR-0018). Uses real history. If a future mechanism can't reproduce this example, the mechanism is wrong (TESTBED rules apply).

## 1. The pattern being tested

- **Family root node** holds everything true of the family as a whole: family-wide dependencies, family-wide mechanisms, iteration records for non-significant versions, marketing aliases.
- **Version nodes exist only where the Significance Filter passes** — for standards this almost always means "introduced a genuinely new dependency."
- **Versions attach to the root in a flat star** (`IS_REFINEMENT_OF → family root`), NOT chained to each other. Chaining (ax → n → g → root) would make requirement inheritance drag version-specific baggage down the chain; succession is story, told with dated `REPLACED_BY`/`SUPERSEDED_BY` edges between versions.
- **Features attach at the granularity where they are true**: family-wide → root; version-specific → edges to exactly the version nodes that have them (non-contiguous is fine); versions without nodes → iteration-record data, **lifted** into edges if that version ever earns a node. Lifting is a pure resolution increase — never wrong, only incomplete (ADR-0015).
- **Consumers link to the family unless a version is their specific truth.** Historical instances link to the version they actually shipped with (most specific truth, ADR-0008); abstract consumers link to the root.

## 2. The cast

**Family root:** `802.11 Wireless LAN` (STANDARD_UNIT). Aliases: "WiFi", "Wi-Fi", "WLAN". Specified by IEEE (org node); "Wi-Fi" branding by the Wi-Fi Alliance (separate org node — the standard and the brand are different actors).

**Family-root dependencies** (true of every version):
| Provider | Edge | Note |
|---|---|---|
| Spread Spectrum (METHOD) | MAKES_POSSIBLE | ← Lamarr/Antheil frequency-hopping *patent work* (ADR-0007: via the work, not the person) |
| CSMA/CA (METHOD) | IS_COMPONENT_OF | lineage: ALOHAnet → CSMA — a Bridge from 1970s packet radio |
| ISM Band Deregulation, FCC 1985 (LEGISLATION) | MAKES_POSSIBLE | legislation as a first-class dependency — no unlicensed spectrum, no WiFi |
| RF Transceiver (TECHNOLOGY) | IS_COMPONENT_OF | |
| Crystal Oscillator (TECHNOLOGY) | IS_COMPONENT_OF | microsecond timing for the MAC (TSF needs this) |

**Version nodes** — each with the Significance rule it passes and the new dependency that earns it:
| Version | Node? | Rule | New dependency (its own lineage shown) |
|---|---|---|---|
| 802.11-1997 | — (it IS the root's founding record) | | |
| 802.11b (1999) | ✅ | Scale — made WiFi a consumer technology | CCK modulation |
| 802.11a (1999) | ✅ | Divergence — the 5 GHz OFDM branch that lost round one | OFDM ← FFT (Cooley–Tukey *work*) ← DSP chips |
| 802.11g (2003) | ✅ | Keystone — OFDM brought to 2.4 GHz, the mass-adoption merge | OFDM + 2.4 GHz coexistence |
| 802.11i (2004) | ✅ | Bridge — into cryptography | AES-CCMP ← AES (NIST standard node) |
| 802.11n / "WiFi 4" (2009) | ✅ | Progenitor of spatial multiplexing in consumer radio | MIMO ← spatial-multiplexing theory (Bell Labs *works*) |
| 802.11ac / "WiFi 5" (2013) | ✅ | new dep | MU-MIMO beamforming |
| 802.11ax / "WiFi 6" (2019) | ✅ | Bridge — OFDMA imported from cellular (LTE) | OFDMA ← cellular scheduling |
| 802.11be / "WiFi 7" (2024) | ✅ | new dep | Multi-Link Operation |
| 802.11d, e, h, j… | ❌ | fails all six | iteration records on the root: `{name:"802.11j", year:2004, key_feature:"Japan 4.9/5.0 GHz bands"}` |

"WiFi 4/5/6/7" are `aliases` on the version nodes — marketing names are search keys, not structure.

**Succession (story layer):** b —REPLACED_BY→ g —REPLACED_BY→ n —… dated; rendering's History Mode shows the generational wave without affecting requirement logic.

## 3. TSF — the actual question that started this

TSF (Timing Synchronization Function) is part of the base 802.11 MAC **since 1997** — true of the whole family. So in reality:

- Node: `TSF` (METHOD_TECHNIQUE), `IS_COMPONENT_OF → 802.11 family root`, dated 1997.
- Its own dependencies: Crystal Oscillator, clock-synchronization concepts.
- A rabbit-holing contributor adds exactly one node and one edge. Done. No version surgery.

**The TB-033 counterfactual** (suppose TSF existed only in WiFi 5–8): then TSF gets `IS_COMPONENT_OF` edges to *exactly* the version nodes that have it — ac, ax, be, next — non-contiguous presence is naturally fine (the GoPro case, TB-006, is this same shape). If one of those versions had no node (say a hypothetical minor version), TSF-presence sits in its iteration record until that version ever earns a node, at which point the record data **lifts** into a real edge. Both states are true; the edge form just has more resolution.

## 4. Consumers

| Consumer | Links to | Why |
|---|---|---|
| iPhone 1 (2007) | 802.11b, 802.11g version nodes | historical instances link to the most specific truth — it shipped b/g |
| Smartphone (abstract paradigm) | family root | abstracts link as high as remains true (every smartphone has *some* WiFi) |
| Standalone VR headset (2023-era) | 802.11ax | genuinely built against WiFi 6 (latency/TWT); a hard link because that's its truth — consistent with "top products use constraints, deep tech uses hard links" the other way: here the version IS the shipped dependency |
| Smart bulb | family root + cost/power constraints on the edge | doesn't care which version; constraints let the (future) solver pick era-appropriate silicon |

**When a new version node appears** (ax is created in 2019): nothing migrates by default — family links remain true (ADR-0015). The re-parenting check queue (Q-04) only *suggests* repointing for consumers whose edge constraints or dates make the new version their more specific truth. Contrast with *interposition* (inserting a node mid-edge), which is the queue's mandatory case.

## 5. Does the pattern generalize?

**Thunderbolt:** root `Thunderbolt` (aliases: Light Peak). TB1/2 iterations records; TB3 ✅ (USB-C connector + dropped Mini DisplayPort — Scale + new dep); TB4 ❌ (certification tightening — iteration record on root, and the best proof the filter works: the *marketing* increment doesn't earn structure); TB5 ✅ (PAM-3 signaling). USB4 is a separate family root with an `ADOPTS → Thunderbolt 3` edge — standards absorbing other standards is an edge, not a merge.

**DDR:** DDR/DDR2…DDR5 — the already-canonical refinement example fits the same star + significance shape.

**CPU fan-out (TB-013):** the dual of the same pattern. One `Microprocessor` role node; architecture divergence is refinement children (x86, ARM, RISC-V); the "hundreds of branches" are **consumer edges, each carrying its own constraints** (pacemaker: µW power; car ECU: −40–125 °C + functional safety; datacenter: perf/watt; smart card: cost + tamper resistance; missile guidance: rad-hard + real-time), with capability routers ("Low-Power Computing", "Real-Time Computing", "High-Performance Computing") bundling recurring demand profiles. Growth is linear-in-consumers (1 edge each) plus sublinear routers — no node explosion, no mush, and zoom/LOD keeps it legible. The Phase 2 seed corridor MUST include this node at real density as the empirical check.

## 6. What this example validates

- Family root + significance-gated version stars handle real standards without node spam (TB-014, TB-015 ✅).
- Feature presence attaches at truth-granularity and lifts monotonically (TB-033, and the mechanism for TB-006's gap ✅).
- Legislation, works-not-people, org-vs-brand, and cross-domain bridges (OFDMA ← cellular) all exercise existing ADRs without new machinery.
- Remaining honest risk: filter judgment calls (is 802.11g Keystone or iteration?) are editorial, not structural — disputes land in the normal moderation/dispute lane (Q-14), and being wrong about *node-worthiness* is recoverable in both directions (create later + lift, or merge + redirect).
