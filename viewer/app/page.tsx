"use client";
/** Planet v0.3 — lazy solves (a question you ask), full-closure focus,
 *  capped neighbor lists, node images, organic arcs underneath. */
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const TILER = process.env.NEXT_PUBLIC_TILER ?? "http://localhost:8748";

type Card = {
  name: string; validity: string; cited: boolean; image_url?: string;
  requires_count: number; requires: any[];
  enables_count: number; enables: any[]; missing?: string;
  versions?: { node_id: string; year: number }[];
};
type Solve = { existence: string; fitness: string; gaps: [string, string][] };

const existenceWords: Record<string, [string, string]> = {
  SATISFIED: ["Provable from recorded dependencies", "#19715f"],
  UNKNOWN: ["Not yet provable", "#b8860b"],
  VIOLATED: ["Impossible as recorded", "#b02a33"],
};
const fitnessWords: Record<string, [string, string]> = {
  SATISFIED: ["fit for its consumers' stated demands", "#19715f"],
  UNKNOWN: ["fitness unresolved", "#b8860b"],
  VIOLATED: ["works, but unfit for stated demands", "#b02a33"],
};

function bookImage(w = 38, h = 46, ring = false): ImageData {
  const r = 2, W = w * r, H = h * r;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d")!;
  if (ring) {
    g.strokeStyle = "#e63946"; g.lineWidth = 3 * r;
    g.beginPath(); g.roundRect(2 * r, 2 * r, W - 4 * r, H - 4 * r, 8 * r); g.stroke();
  } else {
    g.fillStyle = "#fff";
    g.beginPath(); g.roundRect(0, 0, W, H, 6 * r); g.fill();
  }
  return g.getImageData(0, 0, W, H);
}

export default function Home() {
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const seqRef = useRef<number>(-1);
  const selRef = useRef<string | null>(null);
  const [card, setCard] = useState<Card | null>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [solve, setSolve] = useState<Solve | null>(null);
  const [solving, setSolving] = useState(false);
  const [seq, setSeq] = useState(0);
  const [tab, setTab] = useState("Explore");
  const [q, setQ] = useState("");
  // version families the user has "demerged" — collapsed by default
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const expandedRef = useRef<Set<string>>(expanded);
  // the focused closure: PINNED VISIBLE at every zoom (user ruling — a
  // clicked path must never disappear when zooming out)
  const focusRef = useRef<{ n: string[]; e: string[] } | null>(null);

  const applyFilters = (map: maplibregl.Map) => {
    if (!map.getLayer("nodes")) return;
    const fams = ["literal", [...expandedRef.current]] as any;
    const litN = ["literal", focusRef.current?.n ?? []] as any;
    const litE = ["literal", focusRef.current?.e ?? []] as any;
    // zoom LOD (map-style: tiers appear as you zoom; versions auto-tuck),
    // OR manual demerge override, OR membership in the focused closure
    const showNode = ["any", ["<=", ["get", "zmin"], ["zoom"]],
                      ["in", ["get", "family"], fams],
                      ["in", ["get", "node_id"], litN]] as any;
    const showEdge = ["all",
      ["any",
        ["all", ["<=", ["get", "ezmin"], ["zoom"]],
         ["any", ["!", ["has", "zmax"]], ["<", ["zoom"], ["get", "zmax"]]]],
        ["all", ["!", ["get", "lifted"]], ["!=", ["get", "vfamily"], ""],
         ["in", ["get", "vfamily"], fams]],
        ["in", ["get", "edge_id"], litE]],
      // a manually demerged family retires its lifted stand-in edges
      ["any", ["!", ["get", "lifted"]],
       ["!", ["in", ["get", "vfamily"], fams]]]] as any;
    map.setFilter("nodes", showNode);
    map.setFilter("node-ring", ["all", ["!", ["get", "cited"]], showNode]);
    map.setFilter("edges", ["all", ["!", ["get", "ghost"]], showEdge]);
    map.setFilter("edges-casing", ["all", ["!", ["get", "ghost"]], showEdge]);
    map.setFilter("edges-ghost", ["all", ["get", "ghost"], showEdge]);
  };

  const toggleFamily = (fam: string) => {
    const next = new Set(expandedRef.current);
    next.has(fam) ? next.delete(fam) : next.add(fam);
    expandedRef.current = next; setExpanded(next);
    if (mapRef.current) applyFilters(mapRef.current);
  };

  const clearDim = (map: maplibregl.Map) => {
    map.removeFeatureState({ source: "httk", sourceLayer: "nodes" });
    map.removeFeatureState({ source: "httk", sourceLayer: "edges" });
  };

  const applyDim = async (map: maplibregl.Map, id: string) => {
    // full dependency closure, all the way up and all the way down.
    // Edges are FAINT AT REST — focus LIGHTS the closure's threads vivid
    // while everything else recedes (user ruling 2026-08-09).
    const cl = await (await fetch(`${TILER}/closure/${id}`)).json();
    const nodes = new Set<string>(cl.nodes), edges = new Set<string>(cl.edges);
    focusRef.current = { n: cl.nodes, e: cl.edges };
    applyFilters(map);
    clearDim(map);
    for (const f of map.querySourceFeatures("httk", { sourceLayer: "nodes" })) {
      const nid = f.properties?.node_id;
      if (nid && !nodes.has(nid))
        map.setFeatureState({ source: "httk", sourceLayer: "nodes", id: nid },
                            { dim: true });
    }
    for (const f of map.querySourceFeatures("httk", { sourceLayer: "edges" })) {
      const eid = f.properties?.edge_id;
      if (!eid) continue;
      map.setFeatureState({ source: "httk", sourceLayer: "edges", id: eid },
                          edges.has(eid) ? { lit: true } : { dim: true });
    }
  };

  const focusOn = async (map: maplibregl.Map, id: string) => {
    selRef.current = id; setSel(id); setSolve(null);
    setCard(await (await fetch(`${TILER}/node/${id}`)).json());
    applyDim(map, id);
  };

  const askSolve = async () => {
    if (!selRef.current) return;
    setSolving(true);
    setSolve(await (await fetch(`${TILER}/solve/${selRef.current}`)).json());
    setSolving(false);
  };

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapDiv.current!, style: `${TILER}/style.json`,
      center: [0, 10], zoom: 2.2, attributionControl: false,
      renderWorldCopies: false,        // one world — no doubled planets
    });
    mapRef.current = map;
    map.on("load", () => {
      map.addImage("book", bookImage(), { pixelRatio: 2, sdf: true });
      map.addImage("book-ring", bookImage(44, 52, true), { pixelRatio: 2 });
      applyFilters(map);                       // versions start tucked in
    });
    map.on("click", "nodes", (e) => {
      const id = e.features?.[0]?.properties?.node_id;
      if (id) focusOn(map, id);
    });
    map.on("click", (e) => {
      const hits = map.queryRenderedFeatures(e.point, { layers: ["nodes"] });
      if (!hits.length) { clearDim(map); setCard(null); setSel(null); setSolve(null);
                          selRef.current = null;
                          focusRef.current = null; applyFilters(map); }
    });
    map.on("mouseenter", "nodes", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "nodes", () => (map.getCanvas().style.cursor = ""));
    map.on("sourcedata", () => {           // re-apply dim when tiles reload
      if (selRef.current) applyDim(map, selRef.current);
    });

    let fitted = false;
    const poll = setInterval(async () => {
      try {
        const { seq: s, bounds } = await (await fetch(`${TILER}/changes`)).json();
        if (!fitted && bounds) {                 // land on the content, not the ocean
          fitted = true;
          map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]],
                        { padding: 90, duration: 800 });
        }
        if (s !== seqRef.current) {
          seqRef.current = s; setSeq(s);
          (map.getSource("httk") as maplibregl.VectorTileSource)
            ?.setTiles([`${TILER}/tiles/{z}/{x}/{y}.mvt?v=${s}`]);
        }
      } catch { /* tiler down; keep polling */ }
    }, 2000);
    return () => { clearInterval(poll); map.remove(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const doSearch = async (ev: React.FormEvent) => {
    ev.preventDefault();
    const { hits } = await (await fetch(
      `${TILER}/search?q=${encodeURIComponent(q)}`)).json();
    const map = mapRef.current;
    if (hits.length && map) {
      map.flyTo({ center: [hits[0].lng, hits[0].lat], zoom: 5 });
      focusOn(map, hits[0].node_id);
    }
  };

  const S = styles;
  const NeighborList = ({ title, items, total, dir }:
    { title: string; items: any[]; total: number; dir: "from" | "to" }) => (
    <div>
      <h4 style={{ margin: "14px 0 4px" }}>{title} ({total})</h4>
      <ul style={{ margin: 0 }}>
        {items.map((e) => (
          <li key={e.edge_id} style={S.link}
              onClick={() => mapRef.current && focusOn(mapRef.current, e[dir])}>
            {e[dir]} <small style={{ opacity: 0.45 }}>{e.type}</small>
          </li>))}
      </ul>
      {total > items.length &&
        <div style={{ opacity: 0.5, fontSize: 12, marginTop: 2 }}>
          +{total - items.length} more — explore on the map</div>}
    </div>
  );

  return (
    <div style={S.shell}>
      <header style={S.tabs}>
        {["Explore", "Bounties", "Tickets", "Changes"].map((t) => (
          <button key={t} onClick={() => setTab(t)}
                  style={{ ...S.tab, ...(tab === t ? S.tabActive : {}) }}>
            {t}
          </button>
        ))}
        <span style={{ flex: 1 }} />
        <span style={S.seq}>live · log seq {seq}</span>
      </header>
      <main style={S.main}>
        <aside style={S.panel}>
          {!card && <p style={{ opacity: 0.6 }}>Click a node — or search, upper
            right. Red ring = needs citation. Faded = nobody vouched yet.
            Everything builds from zero.</p>}
          {card && !card.missing && (
            <div>
              {card.image_url &&
                <img src={card.image_url} alt="" style={S.img} />}
              <h2 style={{ margin: "4px 0 10px" }}>{card.name}</h2>
              <p>
                <Chip ok={card.validity === "current_truth"}
                      label={`validity: ${card.validity}`} />{" "}
                <Chip ok={card.cited} label={card.cited ? "cited" : "needs citation"} />
              </p>
              {!solve &&
                <button onClick={askSolve} disabled={solving} style={S.solveBtn}>
                  {solving ? "solving…" : "Can this be built? (ask the solver)"}
                </button>}
              {solve && (
                <div style={S.solveBox}>
                  <b style={{ color: existenceWords[solve.existence]?.[1] }}>
                    {existenceWords[solve.existence]?.[0] ?? solve.existence}
                  </b>
                  <div style={{ color: fitnessWords[solve.fitness]?.[1],
                                fontSize: 13 }}>
                    {fitnessWords[solve.fitness]?.[0] ?? solve.fitness}
                  </div>
                  {solve.gaps.length > 0 && (
                    <details open>
                      <summary style={{ color: "#b8860b", cursor: "pointer" }}>
                        {solve.gaps.length} unresolved
                      </summary>
                      <ul>{solve.gaps.slice(0, 12).map(([s, w], i) =>
                        <li key={i} style={{ opacity: 0.8 }}>{s}: {w}</li>)}</ul>
                    </details>)}
                </div>)}
              {sel && (card.versions?.length ?? 0) > 0 && (
                <div style={{ margin: "10px 0" }}>
                  <button onClick={() => toggleFamily(sel)} style={S.solveBtn}>
                    {expanded.has(sel)
                      ? "⊟ Tuck versions back in"
                      : `⊞ Demerge ${card.versions!.length} versions (timeline)`}
                  </button>
                  {expanded.has(sel) && (
                    <ul style={{ margin: "6px 0 0" }}>
                      {card.versions!.map((v) => (
                        <li key={v.node_id} style={S.link}
                            onClick={() => mapRef.current &&
                                           focusOn(mapRef.current, v.node_id)}>
                          {v.node_id}{" "}
                          <small style={{ opacity: 0.45 }}>
                            {v.year || "undated"}</small>
                        </li>))}
                    </ul>)}
                </div>)}
              <NeighborList title="requires" items={card.requires}
                            total={card.requires_count} dir="from" />
              <NeighborList title="enables" items={card.enables}
                            total={card.enables_count} dir="to" />
            </div>
          )}
        </aside>
        <div style={{ position: "relative", flex: 1 }}>
          <div ref={mapDiv} style={{ position: "absolute", inset: 0 }} />
          <form onSubmit={doSearch} style={S.search}>
            <input value={q} onChange={(e) => setQ(e.target.value)}
                   placeholder="Search the tree…" style={S.searchInput} />
          </form>
        </div>
      </main>
    </div>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return <span style={{
    padding: "2px 8px", borderRadius: 10, fontSize: 12,
    background: ok ? "#e8f5ee" : "#fdeaea",
    border: `1px solid ${ok ? "#2a9d8f" : "#e63946"}`,
    color: ok ? "#19715f" : "#b02a33",
  }}>{label}</span>;
}

const styles: Record<string, React.CSSProperties> = {
  shell: { display: "flex", flexDirection: "column", height: "100vh",
           background: "#fff", color: "#1b2432" },
  tabs: { display: "flex", alignItems: "center", gap: 4, padding: "8px 14px",
          borderBottom: "1px solid #e4e8ef" },
  tab: { border: "none", background: "none", padding: "6px 12px", fontSize: 14,
         cursor: "pointer", color: "#5a6577", borderRadius: 8 },
  tabActive: { background: "#eef2f8", color: "#1b2432", fontWeight: 600 },
  seq: { fontSize: 12, color: "#8a93a3" },
  main: { display: "flex", flex: 1, minHeight: 0 },
  panel: { width: 380, padding: 16, overflowY: "auto",
           borderRight: "1px solid #e4e8ef", fontSize: 14 },
  link: { cursor: "pointer" },
  img: { width: "100%", borderRadius: 10, marginBottom: 8,
         border: "1px solid #e4e8ef" },
  solveBtn: { padding: "8px 12px", borderRadius: 10, border: "1px solid #cfd6e0",
              background: "#f6f8fb", cursor: "pointer", fontSize: 13 },
  solveBox: { padding: "10px 12px", borderRadius: 10, background: "#f6f8fb",
              border: "1px solid #e4e8ef", margin: "6px 0" },
  search: { position: "absolute", top: 12, right: 12, zIndex: 5 },
  searchInput: { padding: "8px 12px", borderRadius: 10, width: 240,
                 border: "1px solid #cfd6e0", background: "#fff", fontSize: 14,
                 boxShadow: "0 2px 8px rgba(20,30,50,.08)" },
};
