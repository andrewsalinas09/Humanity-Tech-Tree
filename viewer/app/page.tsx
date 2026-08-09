"use client";
/** The planet, v0: MapLibre over the dynamic tiler, live-refreshing as facts land.
 *  React orchestrates; the graph surface renders itself (ADR-0044 D1). */
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const TILER = process.env.NEXT_PUBLIC_TILER ?? "http://localhost:8748";

type Card = {
  name: string; validity: string; cited: boolean;
  solve: { existence: string; fitness: string; gaps: [string, string][] };
  edges_in: any[]; edges_out: any[]; missing?: string;
};

export default function Home() {
  const mapDiv = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const seqRef = useRef<number>(-1);
  const [card, setCard] = useState<Card | null>(null);
  const [seq, setSeq] = useState(0);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: mapDiv.current!, style: `${TILER}/style.json`,
      center: [0, 0], zoom: 2.2, attributionControl: false,
    });
    mapRef.current = map;
    map.on("click", "nodes", async (e) => {
      const id = e.features?.[0]?.properties?.node_id;
      if (!id) return;
      setCard(await (await fetch(`${TILER}/node/${id}`)).json());
    });
    map.on("mouseenter", "nodes", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "nodes", () => (map.getCanvas().style.cursor = ""));

    const poll = setInterval(async () => {
      try {
        const { seq: s } = await (await fetch(`${TILER}/changes`)).json();
        if (s !== seqRef.current) {
          seqRef.current = s; setSeq(s);
          const src = map.getSource("httk") as maplibregl.VectorTileSource;
          src?.setTiles([`${TILER}/tiles/{z}/{x}/{y}.mvt?v=${s}`]); // live refresh
        }
      } catch { /* tiler down; keep polling */ }
    }, 2000);
    return () => { clearInterval(poll); map.remove(); };
  }, []);

  return (
    <main style={{ display: "flex", height: "100vh" }}>
      <div ref={mapDiv} style={{ flex: 1 }} />
      <aside style={{ width: 360, padding: 16, overflowY: "auto",
                      borderLeft: "1px solid #1e2633", fontSize: 14 }}>
        <div style={{ opacity: 0.5, fontSize: 12 }}>
          Humanity Tech Tree · live · log seq {seq}
        </div>
        {!card && <p style={{ opacity: 0.7 }}>Click a node. Red ring = needs
          citation. Hollow = nobody vouched yet. Everything builds from zero.</p>}
        {card && !card.missing && (
          <div>
            <h2 style={{ margin: "8px 0" }}>{card.name}</h2>
            <p>
              <Chip ok={card.validity === "current_truth"}
                    label={`validity: ${card.validity}`} />{" "}
              <Chip ok={card.cited} label={card.cited ? "cited" : "needs citation"} />
            </p>
            <p>existence: <b>{card.solve.existence}</b> · fitness:{" "}
              <b>{card.solve.fitness}</b></p>
            {card.solve.gaps.length > 0 && (
              <details open>
                <summary style={{ color: "#e9c46a" }}>
                  {card.solve.gaps.length} unresolved (the gap list)
                </summary>
                <ul>{card.solve.gaps.map(([s, w], i) =>
                  <li key={i} style={{ opacity: 0.8 }}>{s}: {w}</li>)}</ul>
              </details>
            )}
            <h4>requires ({card.edges_in.length})</h4>
            <ul>{card.edges_in.map((e) =>
              <li key={e.edge_id}>{e.from} <small style={{ opacity: 0.5 }}>
                {e.type}</small></li>)}</ul>
            <h4>enables ({card.edges_out.length})</h4>
            <ul>{card.edges_out.map((e) =>
              <li key={e.edge_id}>{e.to} <small style={{ opacity: 0.5 }}>
                {e.type}</small></li>)}</ul>
          </div>
        )}
      </aside>
    </main>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return <span style={{
    padding: "2px 8px", borderRadius: 10, fontSize: 12,
    background: ok ? "#1d3b2a" : "#3b1d1d",
    border: `1px solid ${ok ? "#2a9d8f" : "#e63946"}`,
  }}>{label}</span>;
}
