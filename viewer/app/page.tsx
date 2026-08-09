"use client";
/** Planet v0.2 — user rulings: panel LEFT, tabs top, search upper-right,
 *  white world, book-shaped nodes, focus-dimming on selection. */
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const TILER = process.env.NEXT_PUBLIC_TILER ?? "http://localhost:8748";

type Card = {
  name: string; validity: string; cited: boolean;
  solve: { existence: string; fitness: string; gaps: [string, string][] };
  edges_in: any[]; edges_out: any[]; missing?: string;
};

/** A little book, slightly wider than a real one: rounded page + spine. */
function bookImage(w = 38, h = 46, ring = false): ImageData {
  const r = 2, W = w * r, H = h * r;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d")!;
  const rr = (x: number, y: number, ww: number, hh: number, rad: number) => {
    g.beginPath();
    g.roundRect(x, y, ww, hh, rad);
  };
  if (ring) {
    g.strokeStyle = "#e63946"; g.lineWidth = 3 * r;
    rr(2 * r, 2 * r, W - 4 * r, H - 4 * r, 8 * r); g.stroke();
  } else {
    g.fillStyle = "#fff";                       // SDF alpha shape (tinted by style)
    rr(0, 0, W, H, 6 * r); g.fill();
  }
  return g.getImageData(0, 0, W, H);
}

export default function Home() {
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const seqRef = useRef<number>(-1);
  const [card, setCard] = useState<Card | null>(null);
  const [seq, setSeq] = useState(0);
  const [tab, setTab] = useState("Explore");
  const [q, setQ] = useState("");

  const clearDim = (map: maplibregl.Map) => {
    map.removeFeatureState({ source: "httk", sourceLayer: "nodes" });
    map.removeFeatureState({ source: "httk", sourceLayer: "edges" });
  };

  const focusOn = async (map: maplibregl.Map, id: string) => {
    const data: Card = await (await fetch(`${TILER}/node/${id}`)).json();
    setCard(data);
    if (data.missing) return;
    const family = new Set<string>([id]);
    data.edges_in.forEach((e: any) => family.add(e.from));
    data.edges_out.forEach((e: any) => family.add(e.to));
    const keepEdges = new Set<string>(
      [...data.edges_in, ...data.edges_out].map((e: any) => e.edge_id));
    clearDim(map);
    for (const f of map.querySourceFeatures("httk", { sourceLayer: "nodes" })) {
      const nid = f.properties?.node_id;
      if (nid && !family.has(nid))
        map.setFeatureState({ source: "httk", sourceLayer: "nodes", id: nid },
                            { dim: true });
    }
    for (const f of map.querySourceFeatures("httk", { sourceLayer: "edges" })) {
      const eid = f.properties?.edge_id;
      if (eid && !keepEdges.has(eid))
        map.setFeatureState({ source: "httk", sourceLayer: "edges", id: eid },
                            { dim: true });
    }
  };

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapDiv.current!, style: `${TILER}/style.json`,
      center: [0, 20], zoom: 2.2, attributionControl: false,
    });
    mapRef.current = map;
    map.on("load", () => {
      map.addImage("book", bookImage(), { pixelRatio: 2, sdf: true });
      map.addImage("book-ring", bookImage(44, 52, true), { pixelRatio: 2 });
    });
    map.on("click", "nodes", (e) => {
      const id = e.features?.[0]?.properties?.node_id;
      if (id) focusOn(map, id);
    });
    map.on("click", (e) => {
      const hits = map.queryRenderedFeatures(e.point, { layers: ["nodes"] });
      if (!hits.length) { clearDim(map); setCard(null); }   // background: unfocus
    });
    map.on("mouseenter", "nodes", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "nodes", () => (map.getCanvas().style.cursor = ""));

    const poll = setInterval(async () => {
      try {
        const { seq: s } = await (await fetch(`${TILER}/changes`)).json();
        if (s !== seqRef.current) {
          seqRef.current = s; setSeq(s);
          (map.getSource("httk") as maplibregl.VectorTileSource)
            ?.setTiles([`${TILER}/tiles/{z}/{x}/{y}.mvt?v=${s}`]);
        }
      } catch { /* tiler down; keep polling */ }
    }, 2000);
    return () => { clearInterval(poll); map.remove(); };
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
              <h2 style={{ margin: "4px 0 10px" }}>{card.name}</h2>
              <p>
                <Chip ok={card.validity === "current_truth"}
                      label={`validity: ${card.validity}`} />{" "}
                <Chip ok={card.cited} label={card.cited ? "cited" : "needs citation"} />
              </p>
              <p>existence: <b>{card.solve.existence}</b><br />
                 fitness: <b>{card.solve.fitness}</b></p>
              {card.solve.gaps.length > 0 && (
                <details open>
                  <summary style={{ color: "#b8860b", cursor: "pointer" }}>
                    {card.solve.gaps.length} unresolved (the gap list)
                  </summary>
                  <ul>{card.solve.gaps.map(([s, w], i) =>
                    <li key={i} style={{ opacity: 0.8 }}>{s}: {w}</li>)}</ul>
                </details>
              )}
              <h4>requires ({card.edges_in.length})</h4>
              <ul>{card.edges_in.map((e) =>
                <li key={e.edge_id} style={S.link}
                    onClick={() => mapRef.current && focusOn(mapRef.current, e.from)}>
                  {e.from} <small style={{ opacity: 0.45 }}>{e.type}</small></li>)}</ul>
              <h4>enables ({card.edges_out.length})</h4>
              <ul>{card.edges_out.map((e) =>
                <li key={e.edge_id} style={S.link}
                    onClick={() => mapRef.current && focusOn(mapRef.current, e.to)}>
                  {e.to} <small style={{ opacity: 0.45 }}>{e.type}</small></li>)}</ul>
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
  search: { position: "absolute", top: 12, right: 12, zIndex: 5 },
  searchInput: { padding: "8px 12px", borderRadius: 10, width: 240,
                 border: "1px solid #cfd6e0", background: "#fff", fontSize: 14,
                 boxShadow: "0 2px 8px rgba(20,30,50,.08)" },
};
