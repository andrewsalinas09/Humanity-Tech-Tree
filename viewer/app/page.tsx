"use client";
/** Planet v0.3 — lazy solves (a question you ask), full-closure focus,
 *  capped neighbor lists, node images, organic arcs underneath. */
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const TILER = process.env.NEXT_PUBLIC_TILER ?? "http://localhost:8748";

type EdgeView = {
  edge_id: string; other: string; other_name: string; type: string;
  qualifier: string; year?: number; justification?: string;
  shadowed: boolean; alt_group?: number | null;
};
type Card = {
  name: string; category: string; description?: string;
  aliases: string[]; validity: string; cited: boolean;
  citations: { claim: string; source: string; source_name: string;
               locator?: string }[];
  image_url?: string;
  requires_count: number; requires: EdgeView[]; or_group_count: number;
  enables_count: number; enables: EdgeView[];
  story: EdgeView[]; missing?: string;
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
  const [reqs, setReqs] = useState<any[]>([]);
  const [board, setBoard] = useState<any[]>([]);
  const [form, setForm] = useState({ want: "WANT_NODE", subject_node: "",
                                     wanted_name: "", notes: "", sources: "" });

  const loadRequests = async () => {
    setReqs(await (await fetch(`${TILER}/requests?status=all`)).json());
    setBoard(await (await fetch(`${TILER}/leaderboard`)).json());
  };

  const postRequest = async (ev: React.FormEvent) => {
    ev.preventDefault();
    const sources = form.sources.trim()
      ? form.sources.split("\n").map((l) => {
          const [source, locator] = l.split("|").map((s) => s.trim());
          return { source, locator: locator ?? null };
        }) : [];
    const body: any = { want: form.want, notes: form.notes || null,
                        offered_sources: sources };
    if (form.want === "WANT_NODE") body.wanted_name = form.wanted_name;
    else body.subject_node = form.subject_node;
    const res = await (await fetch(`${TILER}/requests`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body) })).json();
    if (res.rejected) alert(`${res.rejected.rule}: ${res.rejected.message}`);
    else setForm({ ...form, wanted_name: "", subject_node: "", notes: "",
                   sources: "" });
    loadRequests();
  };

  const endorse = async (id: number) => {
    await fetch(`${TILER}/requests/${id}/endorse`, { method: "POST",
      headers: { "Content-Type": "application/json" }, body: "{}" });
    loadRequests();
  };

  const [who, setWho] = useState<any | null>(null);
  const loadLeaders = async () => {
    setBoard(await (await fetch(`${TILER}/leaderboard`)).json());
    setWho(null);
  };
  const openWho = async (id: string) => {
    setWho(await (await fetch(`${TILER}/contributions/${id}`)).json());
  };

  const reopen = async (id: number) => {
    const reason = window.prompt("Why does this need re-opening?");
    if (!reason) return;
    await fetch(`${TILER}/requests/${id}/reopen`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }) });
    loadRequests();
  };
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
  const qualifierWords: Record<string, string> = {
    authored: "authored by", documents: "documented in",
    invented: "invented by", discovered: "discovered by",
    replaced: "replaced by",
  };
  const EdgeLine = ({ e }: { e: EdgeView }) => (
    <li style={{ ...S.link, opacity: e.shadowed ? 0.5 : 1 }}
        onClick={() => mapRef.current && focusOn(mapRef.current, e.other)}
        title={e.justification ?? undefined}>
      {e.other_name}
      <small style={{ opacity: 0.5 }}>
        {" "}{e.qualifier
          ? (qualifierWords[e.qualifier] ?? e.qualifier)
          : e.type.toLowerCase().replace(/_/g, " ")}
        {e.year ? ` · ${Math.trunc(e.year)}` : ""}
        {e.shadowed ? " · shadowed" : ""}
      </small>
    </li>
  );
  const RequiresList = ({ items, total }:
    { items: EdgeView[]; total: number }) => {
    const always = items.filter((e) => e.alt_group == null);
    const groups = new Map<number, EdgeView[]>();
    for (const e of items)
      if (e.alt_group != null)
        groups.set(e.alt_group, [...(groups.get(e.alt_group) ?? []), e]);
    return (
      <div>
        <h4 style={{ margin: "14px 0 4px" }}>requires ({total})</h4>
        <ul style={{ margin: 0 }}>{always.map((e) =>
          <EdgeLine key={e.edge_id} e={e} />)}</ul>
        {groups.size > 0 && (
          <div style={S.orBox}>
            <div style={S.orTitle}>either path:</div>
            {[...groups.entries()].map(([gi, ge], idx) => (
              <div key={gi}>
                {idx > 0 && <div style={S.orSep}>— or —</div>}
                <ul style={{ margin: 0 }}>{ge.map((e) =>
                  <EdgeLine key={e.edge_id} e={e} />)}</ul>
              </div>))}
          </div>)}
        {total > items.length &&
          <div style={{ opacity: 0.5, fontSize: 12, marginTop: 2 }}>
            +{total - items.length} more — explore on the map</div>}
      </div>
    );
  };
  const NeighborList = ({ title, items, total }:
    { title: string; items: EdgeView[]; total: number }) => (
    <div>
      <h4 style={{ margin: "14px 0 4px" }}>{title} ({total})</h4>
      <ul style={{ margin: 0 }}>
        {items.map((e) => <EdgeLine key={e.edge_id} e={e} />)}
      </ul>
      {total > items.length &&
        <div style={{ opacity: 0.5, fontSize: 12, marginTop: 2 }}>
          +{total - items.length} more — explore on the map</div>}
    </div>
  );

  return (
    <div style={S.shell}>
      <header style={S.tabs}>
        {["Explore", "Bounties", "Leaders", "Tickets", "Changes"].map((t) => (
          <button key={t}
                  onClick={() => { setTab(t);
                                   if (t === "Bounties") loadRequests();
                                   if (t === "Leaders") loadLeaders(); }}
                  style={{ ...S.tab, ...(tab === t ? S.tabActive : {}) }}>
            {t}
          </button>
        ))}
        <span style={{ flex: 1 }} />
        <span style={S.seq}>live · log seq {seq}</span>
      </header>
      <main style={S.main}>
        <aside style={S.panel}>
          {tab === "Bounties" && (
            <div>
              <h3 style={{ margin: "0 0 8px" }}>Ask for something</h3>
              <form onSubmit={postRequest}>
                <select value={form.want}
                        onChange={(e) => setForm({ ...form, want: e.target.value })}
                        style={S.input}>
                  <option value="WANT_NODE">Something should exist</option>
                  <option value="WANT_COVERAGE">Flesh out a node's dependencies</option>
                  <option value="WANT_EVIDENCE">A node needs citations</option>
                </select>
                {form.want === "WANT_NODE"
                  ? <input placeholder="What should exist?" value={form.wanted_name}
                           onChange={(e) => setForm({ ...form, wanted_name: e.target.value })}
                           style={S.input} required />
                  : <input placeholder="node id (e.g. transistor)" value={form.subject_node}
                           onChange={(e) => setForm({ ...form, subject_node: e.target.value })}
                           style={S.input} required />}
                <textarea placeholder="Notes (why / what would make this good)"
                          value={form.notes} rows={2}
                          onChange={(e) => setForm({ ...form, notes: e.target.value })}
                          style={S.input} />
                <textarea placeholder={"Sources you already have, one per line:\nsource | locator"}
                          value={form.sources} rows={2}
                          onChange={(e) => setForm({ ...form, sources: e.target.value })}
                          style={S.input} />
                <button type="submit" style={S.solveBtn}>Post request</button>
              </form>
              <h3 style={{ margin: "16px 0 4px" }}>Queue</h3>
              {reqs.length === 0 && <p style={{ opacity: 0.5 }}>No requests yet.</p>}
              {reqs.map((r) => (
                <div key={r.request} style={S.reqBox}>
                  <div>
                    <b>{r.wanted_name ?? r.subject_node}</b>{" "}
                    <small style={{ opacity: 0.55 }}>
                      {r.want.replace("WANT_", "").toLowerCase()}
                      {" · by "}{r.requested_by?.id}
                    </small>
                  </div>
                  {r.notes && <div style={{ fontSize: 12.5, opacity: 0.75,
                                            whiteSpace: "pre-wrap" }}>{r.notes}</div>}
                  {(r.offered_sources ?? []).length > 0 &&
                    <div style={{ fontSize: 12, opacity: 0.65 }}>
                      📎 {r.offered_sources.map((s: any) =>
                            s.locator ? `${s.source} — ${s.locator}` : s.source)
                          .join(" · ")}</div>}
                  <div style={{ marginTop: 4 }}>
                    {r.status === "open" ? (
                      <button onClick={() => endorse(r.request)} style={S.miniBtn}>
                        ▲ {r.endorsements}
                      </button>
                    ) : (
                      <>
                        <Chip ok label={`fulfilled by ${r.fulfilled_by?.id}`} />{" "}
                        {(r.fulfilled_links ?? []).map((l: string) => (
                          <span key={l} style={{ ...S.link, fontSize: 12,
                                                 marginRight: 6 }}
                                onClick={() => { setTab("Explore");
                                  mapRef.current && focusOn(mapRef.current, l); }}>
                            {l}
                          </span>))}
                        <button onClick={() => reopen(r.request)}
                                style={S.miniBtn}>re-open</button>
                      </>
                    )}
                  </div>
                </div>))}
              {board.length > 0 && (
                <div>
                  <h3 style={{ margin: "16px 0 4px" }}>Karma</h3>
                  {board.map((b) => (
                    <div key={b.id} style={{ fontSize: 13 }}>
                      {b.points} · {b.id} <small style={{ opacity: 0.5 }}>{b.type}</small>
                    </div>))}
                </div>)}
            </div>
          )}
          {tab === "Leaders" && (
            <div>
              {!who && (<>
                <h3 style={{ margin: "0 0 8px" }}>Leaderboard</h3>
                {board.map((b, i) => (
                  <div key={b.id} style={{ ...S.reqBox, cursor: "pointer" }}
                       onClick={() => openWho(b.id)}>
                    <b>#{i + 1} {b.id}</b>{" "}
                    <small style={{ opacity: 0.5 }}>{b.type}</small>
                    <div style={{ fontSize: 12.5, opacity: 0.7 }}>
                      {b.points} karma · {b.facts} facts on the record
                    </div>
                  </div>))}
              </>)}
              {who && (
                <div>
                  <button onClick={() => setWho(null)} style={S.miniBtn}>
                    ← back</button>
                  <h3 style={{ margin: "8px 0 2px" }}>{who.id}</h3>
                  <div style={{ opacity: 0.65, fontSize: 13, marginBottom: 8 }}>
                    {who.points} karma ·{" "}
                    {Object.entries(who.counts as Record<string, number>)
                      .map(([k, v]) => `${v} ${k}`).join(" · ")}
                  </div>
                  {who.fulfilled.length > 0 && (<>
                    <h4 style={{ margin: "10px 0 4px" }}>fulfilled requests</h4>
                    {who.fulfilled.map((f: any) => (
                      <div key={f.request} style={{ fontSize: 13 }}>
                        #{f.request} · {f.want.replace("WANT_", "").toLowerCase()}
                        {" · "}{f.about}
                      </div>))}
                  </>)}
                  <h4 style={{ margin: "10px 0 4px" }}>on the record</h4>
                  {who.recent.map((a: any) => (
                    <div key={a.seq} style={{ fontSize: 12.5, margin: "3px 0" }}>
                      <span style={a.subject ? S.link : undefined}
                            onClick={() => { if (a.subject) { setTab("Explore");
                              mapRef.current && focusOn(mapRef.current, a.subject); } }}>
                        {a.line}
                      </span>
                      <small style={{ opacity: 0.4 }}> · seq {a.seq}</small>
                    </div>))}
                </div>)}
            </div>
          )}
          {tab !== "Bounties" && tab !== "Leaders" && !card &&
            <p style={{ opacity: 0.6 }}>Click a node — or search, upper
            right. Red ring = needs citation. Faded = nobody vouched yet.
            Everything builds from zero.</p>}
          {tab !== "Bounties" && tab !== "Leaders" && card && !card.missing && (
            <div>
              {card.image_url &&
                <img src={card.image_url} alt="" style={S.img} />}
              <h2 style={{ margin: "4px 0 4px" }}>{card.name}</h2>
              {card.aliases.length > 0 &&
                <div style={{ opacity: 0.55, fontSize: 12, marginBottom: 6 }}>
                  also: {card.aliases.join(" · ")}</div>}
              <p style={{ margin: "4px 0 8px" }}>
                <Chip ok label={card.category.toLowerCase().replace(/_/g, " ")} />{" "}
                <Chip ok={card.validity === "current_truth"}
                      label={`validity: ${card.validity}`} />{" "}
                <Chip ok={card.cited} label={card.cited ? "cited" : "needs citation"} />
              </p>
              {card.description
                ? <p style={S.desc}>{card.description}</p>
                : <p style={{ ...S.desc, opacity: 0.45, fontStyle: "italic" }}>
                    No description yet — this node needs one.</p>}
              {card.citations.length > 0 && (
                <div style={{ fontSize: 12, margin: "6px 0" }}>
                  {card.citations.map((c, i) => (
                    <div key={i} style={{ opacity: 0.7 }}>
                      📖 <span style={S.link}
                            onClick={() => mapRef.current &&
                                           focusOn(mapRef.current, c.source)}>
                        {c.source_name}</span>
                      {c.locator ? ` — ${c.locator}` : ""}
                    </div>))}
                </div>)}
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
              <RequiresList items={card.requires} total={card.requires_count} />
              <NeighborList title="enables" items={card.enables}
                            total={card.enables_count} />
              {card.story.length > 0 &&
                <NeighborList title="story & sources" items={card.story}
                              total={card.story.length} />}
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
  desc: { fontSize: 13.5, lineHeight: 1.5, color: "#2a3242",
          margin: "6px 0 10px" },
  orBox: { border: "1px dashed #cfd6e0", borderRadius: 10,
           padding: "6px 10px", margin: "8px 0" },
  orTitle: { fontSize: 11, textTransform: "uppercase", letterSpacing: 0.6,
             color: "#8a93a3", marginBottom: 4 },
  orSep: { textAlign: "center", fontSize: 11, color: "#b0b8c6",
           margin: "2px 0" },
  input: { display: "block", width: "100%", margin: "6px 0", padding: "7px 10px",
           borderRadius: 8, border: "1px solid #cfd6e0", fontSize: 13,
           background: "#fff", color: "#1b2432" },
  reqBox: { border: "1px solid #e4e8ef", borderRadius: 10, padding: "8px 10px",
            margin: "8px 0" },
  miniBtn: { padding: "2px 10px", borderRadius: 8, border: "1px solid #cfd6e0",
             background: "#f6f8fb", cursor: "pointer", fontSize: 12,
             marginRight: 6 },
  solveBox: { padding: "10px 12px", borderRadius: 10, background: "#f6f8fb",
              border: "1px solid #e4e8ef", margin: "6px 0" },
  search: { position: "absolute", top: 12, right: 12, zIndex: 5 },
  searchInput: { padding: "8px 12px", borderRadius: 10, width: 240,
                 border: "1px solid #cfd6e0", background: "#fff", fontSize: 14,
                 boxShadow: "0 2px 8px rgba(20,30,50,.08)" },
};
