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
  const [dels, setDels] = useState<any[]>([]);
  const loadDeletions = async () => {
    setDels(await (await fetch(`${TILER}/deletions`)).json());
  };

  // ---- authoring client (every server capability, FE-accessible) ----------
  const api = async (path: string, body: any) =>
    (await fetch(`${TILER}${path}`, { method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body) })).json();

  const [showAdd, setShowAdd] = useState(false);
  const [add, setAdd] = useState({ name: "", category: "TECHNOLOGY",
                                   description: "", vouch: true });
  const [gateRes, setGateRes] = useState<any | null>(null);
  const [tool, setTool] = useState<string | null>(null);
  const [link, setLink] = useState({ rel: "is enabled by", target: "",
                                     just: "", year: "" });
  const [fields, setFields] = useState<any | null>(null);
  const [cite, setCite] = useState({ aid: "", source: "", locator: "" });
  const [tickets, setTickets] = useState<any[]>([]);
  const [challenges, setChallenges] = useState<any[]>([]);

  const CATEGORIES = ["TECHNOLOGY", "MATERIAL", "METHOD_TECHNIQUE",
    "NATURAL_LAW", "NATURAL_PHENOMENON", "FORMAL_CONCEPT", "CAPABILITY",
    "STANDARD_UNIT", "WORK_PUBLICATION", "LEGISLATION", "HISTORICAL_EVENT",
    "SOCIETAL_ERA", "SOCIETAL_NEED", "BELIEF_SYSTEM", "BIOLOGICAL_ENTITY",
    "ORGANIZATION", "GEOPOLITICAL_ENTITY", "BRAND"];

  const afterCreate = (res: any) => {
    if (res.rejected) { alert(`${res.rejected.rule}: ${res.rejected.message}`); return; }
    const nid = res.applied?.created?.nodes?.[0];
    setShowAdd(false); setGateRes(null);
    setAdd({ name: "", category: "TECHNOLOGY", description: "", vouch: true });
    if (nid && mapRef.current) {
      const m = mapRef.current;
      setTimeout(() => focusOn(m, nid), 2600);   // next tile poll picks it up
    }
  };

  const runGate = async () =>
    setGateRes(await api("/gate", { query: add.name }));

  const createNode = async () => {
    const res = await api("/propose", {
      name: add.name, category: add.category,
      description: add.description || null,
      validity: add.vouch ? "current_truth" : null,
      search_receipt: gateRes?.receipt });
    if (res.ticket) {
      const dupes = (res.options ?? []).filter((o: any) => o.node_id)
        .map((o: any) => o.node_id).join(", ");
      if (window.confirm(`Exact-ish duplicates exist: ${dupes}. Create anyway?`)) {
        afterCreate(await api(`/tickets/${res.ticket}/resolve`, {
          choice: { key: "create_anyway" },
          justification: "distinct concept (decided in viewer)" }));
      }
      return;
    }
    afterCreate(res);
  };

  const REL: Record<string, (s: string, t: string) => { name: string; params: any }> = {
    "is enabled by": (s, t) => ({ name: "add_enabler", params: { enabled: s, enabler: t } }),
    "enables": (s, t) => ({ name: "add_enabler", params: { enabled: t, enabler: s } }),
    "has component": (s, t) => ({ name: "add_component", params: { whole: s, part: t } }),
    "is component of": (s, t) => ({ name: "add_component", params: { whole: t, part: s } }),
    "has ingredient": (s, t) => ({ name: "add_ingredient", params: { product: s, ingredient: t } }),
    "has version": (s, t) => ({ name: "refine", params: { family: s, version: t } }),
    "is succeeded by": (s, t) => ({ name: "succeed", params: { old: s, new: t, qualifier: "replaced" } }),
    "is associated with": (s, t) => ({ name: "associate", params: { a: s, b: t, qualifier: "related" } }),
  };

  const submitLink = async () => {
    const self = selRef.current;
    if (!self || !link.target.trim()) return;
    const mk = REL[link.rel](self, link.target.trim());
    const params: any = { ...mk.params };
    if (link.just && ["add_enabler", "add_component", "add_ingredient"]
        .includes(mk.name)) params.justification = link.just;
    if (link.year && mk.name !== "associate")
      params.start = { year: parseFloat(link.year), unc: 0.5 };
    const res = await api("/verb", { name: mk.name, params });
    if (res.rejected) alert(`${res.rejected.rule}: ${res.rejected.message}`);
    else if (res.ticket) alert(`Decision ticket #${res.ticket} — resolve it in the Tickets tab`);
    else { setTool(null); setLink({ ...link, target: "", just: "", year: "" });
           if (mapRef.current) focusOn(mapRef.current, self); }
  };

  const openCite = async () => {
    setTool("cite");
    setFields(await (await fetch(`${TILER}/nodefields/${selRef.current}`)).json());
  };

  const submitCite = async () => {
    if (!cite.aid || !cite.source) return;
    const res = await api("/verb", { name: "attach_citation",
      params: { assertion_id: cite.aid, source_node: cite.source,
                locator: cite.locator || null } });
    if (res.rejected) alert(`${res.rejected.rule}: ${res.rejected.message}`);
    else { setTool(null); setCite({ aid: "", source: "", locator: "" });
           if (mapRef.current && selRef.current) focusOn(mapRef.current, selRef.current); }
  };

  const confirmClaim = async (aid: string) => {
    const res = await api("/confirm", { assertion_id: aid });
    alert(res.applied ? "Confirmed (human verification, L4)."
                      : `${res.rejected?.rule}: ${res.rejected?.message}`);
  };

  const dispute = async () => {
    const grounds = window.prompt("What's wrong here? (grounds — recorded forever)");
    if (!grounds) return;
    const res = await api("/challenges", { subject: selRef.current, grounds });
    alert(res.challenge ? `Challenge ${res.challenge} opened — voting in the Tickets tab.`
                        : JSON.stringify(res.rejected ?? res));
  };

  const markDelete = async () => {
    const reason = window.prompt("Reason for deletion request (admin approves):");
    if (!reason) return;
    const res = await api("/delete-request",
                          { subject_id: selRef.current, reason });
    alert(res.ticket ? `Delete ticket #${res.ticket} opened.`
                     : JSON.stringify(res.rejected ?? res));
  };

  const loadTickets = async () => {
    setTickets(await (await fetch(`${TILER}/tickets`)).json());
    const ch = await (await fetch(`${TILER}/challenges`)).json();
    for (const c of ch)
      c.tally = await (await fetch(`${TILER}/challenges/${c.challenge}/tally`)).json();
    setChallenges(ch);
  };

  const resolveTicket = async (t: any, opt: any) => {
    const choice: any = { key: opt.key };
    if (opt.node_id) choice.node_id = opt.node_id;
    if ("exclude" in opt) {
      const x = window.prompt("Providers to EXCLUDE from the hoist (comma-separated ids):", "");
      if (x === null) return;
      choice.exclude = x.split(",").map((s) => s.trim()).filter(Boolean);
    }
    if ("include" in opt) {
      const x = window.prompt("ONLY hoist these providers (comma-separated ids):", "");
      if (x === null) return;
      choice.include = x.split(",").map((s) => s.trim()).filter(Boolean);
    }
    const just = opt.justification_required
      ? window.prompt("Justification (required):") : null;
    if (opt.justification_required && !just) return;
    const res = await api(`/tickets/${t.ticket}/resolve`,
                          { choice, justification: just });
    if (res.rejected) alert(`${res.rejected.rule}: ${res.rejected.message}`);
    loadTickets();
  };

  const voteCh = async (cid: string, support: boolean) => {
    const reason = window.prompt("Your reason (votes carry reasons, forever):");
    if (!reason) return;
    await api(`/challenges/${cid}/vote`, { support, reason });
    loadTickets();
  };

  const resolveCh = async (cid: string, outcome: string) => {
    const res = await api(`/challenges/${cid}/resolve`, { outcome });
    if (res.rejected) alert(`${res.rejected.rule}: ${res.rejected.message}`);
    loadTickets();
  };
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
                                   if (t === "Leaders") loadLeaders();
                                   if (t === "Tickets") loadTickets();
                                   if (t === "Changes") loadDeletions(); }}
                  style={{ ...S.tab, ...(tab === t ? S.tabActive : {}) }}>
            {t}
          </button>
        ))}
        <button onClick={() => { setTab("Explore"); setShowAdd(true);
                                 setGateRes(null); }}
                style={{ ...S.tab, fontWeight: 600, color: "#2f6fd0" }}>
          + Add node
        </button>
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
                    {r.status !== "fulfilled" ? (
                      <>
                        {r.status === "reopened" &&
                          <Chip ok={false} label="re-opened" />}{" "}
                        <button onClick={() => endorse(r.request)} style={S.miniBtn}>
                          ▲ {r.endorsements}
                        </button>
                      </>
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
                  <h3 style={{ margin: "16px 0 4px" }}>Ink</h3>
                  {board.map((b) => (
                    <div key={b.id} style={{ fontSize: 13 }}>
                      🖋 {b.ink} · {b.id} <small style={{ opacity: 0.5 }}>{b.type}</small>
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
                    <small style={{ opacity: 0.5 }}>
                      {b.type}{b.operator ? ` · runs under ${b.operator}` : ""}
                    </small>
                    <div style={{ fontSize: 12.5, opacity: 0.7 }}>
                      🖋 {b.ink} ink · rep {b.reputation} · {b.facts} facts
                      on the record
                    </div>
                  </div>))}
              </>)}
              {who && (
                <div>
                  <button onClick={() => setWho(null)} style={S.miniBtn}>
                    ← back</button>
                  <h3 style={{ margin: "8px 0 2px" }}>{who.id}</h3>
                  <div style={{ opacity: 0.65, fontSize: 13, marginBottom: 8 }}>
                    🖋 {who.ink} ink · rep {who.reputation}
                    {who.operator ? ` · runs under ${who.operator}` : ""}
                    {who.operates?.length
                      ? ` · operates: ${who.operates.join(", ")}` : ""}
                    <br />
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
          {tab === "Explore" && showAdd && (
            <div>
              <h3 style={{ margin: "0 0 8px" }}>Add a node</h3>
              <input placeholder="Name (e.g. Samsung Galaxy)" value={add.name}
                     onChange={(e) => setAdd({ ...add, name: e.target.value })}
                     style={S.input} />
              {!gateRes && (
                <button onClick={runGate} style={S.solveBtn}
                        disabled={!add.name.trim()}>
                  Check if it exists (the gate)
                </button>)}
              {gateRes && (
                <div>
                  {gateRes.matches.length > 0 && (<>
                    <h4 style={{ margin: "10px 0 4px" }}>name matches</h4>
                    {gateRes.matches.map((m: any) => (
                      <div key={m.node_id} style={{ ...S.link, fontSize: 13 }}
                           onClick={() => { setShowAdd(false);
                             mapRef.current && focusOn(mapRef.current, m.node_id); }}>
                        {m.node_id} <small style={{ opacity: 0.5 }}>{m.category}</small>
                      </div>))}
                  </>)}
                  {(gateRes.semantic ?? []).length > 0 && (<>
                    <h4 style={{ margin: "10px 0 4px" }}>similar by meaning</h4>
                    {gateRes.semantic.map((s: any) => (
                      <div key={s.node_id} style={S.reqBox}>
                        <span style={S.link}
                              onClick={() => { setShowAdd(false);
                                mapRef.current && focusOn(mapRef.current, s.node_id); }}>
                          {s.name}</span>{" "}
                        <small style={{ opacity: 0.5 }}>{s.score}</small>
                        <div style={{ fontSize: 12, opacity: 0.65 }}>
                          {(s.description ?? "").slice(0, 110)}</div>
                      </div>))}
                    <p style={{ fontSize: 12, opacity: 0.6 }}>
                      If one of these IS your concept, click it instead of
                      creating a duplicate.</p>
                  </>)}
                  <select value={add.category} style={S.input}
                          onChange={(e) => setAdd({ ...add, category: e.target.value })}>
                    {CATEGORIES.map((c) => <option key={c} value={c}>
                      {c.toLowerCase().replace(/_/g, " ")}</option>)}
                  </select>
                  <textarea placeholder="Description: what it is + why it matters (2-3 sentences)"
                            value={add.description} rows={3}
                            onChange={(e) => setAdd({ ...add, description: e.target.value })}
                            style={S.input} />
                  <label style={{ fontSize: 12.5, display: "block", margin: "4px 0" }}>
                    <input type="checkbox" checked={add.vouch}
                           onChange={(e) => setAdd({ ...add, vouch: e.target.checked })} />
                    {" "}I personally vouch this exists (validity: current truth)
                  </label>
                  <button onClick={createNode} style={S.solveBtn}>Create</button>
                </div>)}
              <div style={{ marginTop: 8 }}>
                <button onClick={() => { setShowAdd(false); setGateRes(null); }}
                        style={S.miniBtn}>cancel</button>
              </div>
            </div>
          )}
          {tab === "Tickets" && (
            <div>
              <h3 style={{ margin: "0 0 4px" }}>Decision tickets</h3>
              {tickets.length === 0 && <p style={{ opacity: 0.5 }}>Queue empty.</p>}
              {tickets.map((t) => (
                <div key={t.ticket} style={S.reqBox}>
                  <b>#{t.ticket}</b>{" "}
                  <small style={{ opacity: 0.55 }}>{t.verb}</small>
                  <div style={{ fontSize: 12.5, opacity: 0.8,
                                margin: "3px 0" }}>{t.reason}</div>
                  <div>
                    {t.options.map((o: any, i: number) => (
                      <button key={i} onClick={() => resolveTicket(t, o)}
                              style={S.miniBtn}>
                        {o.key}{o.node_id ? `: ${o.node_id}` : ""}
                      </button>))}
                  </div>
                </div>))}
              <h3 style={{ margin: "16px 0 4px" }}>Challenges</h3>
              {challenges.length === 0 && <p style={{ opacity: 0.5 }}>No disputes.</p>}
              {challenges.map((c) => (
                <div key={c.challenge} style={S.reqBox}>
                  <b style={S.link}
                     onClick={() => { setTab("Explore");
                       mapRef.current && focusOn(mapRef.current, c.subject); }}>
                    {c.subject}</b>{" "}
                  <Chip ok={c.status !== "open"}
                        label={c.status} />
                  <div style={{ fontSize: 12.5, opacity: 0.8 }}>{c.grounds}</div>
                  {c.tally && (
                    <div style={{ fontSize: 12, margin: "4px 0" }}>
                      ⚖ support {c.tally.support} · oppose {c.tally.oppose}
                      {c.tally.votes.map((v: any, i: number) => (
                        <div key={i} style={{ opacity: 0.65 }}>
                          {v.support ? "▲" : "▼"} {v.by} (w{v.weight}): {v.reason}
                        </div>))}
                    </div>)}
                  {c.status === "open" && (<>
                    <button onClick={() => voteCh(c.challenge, true)}
                            style={S.miniBtn}>▲ support</button>
                    <button onClick={() => voteCh(c.challenge, false)}
                            style={S.miniBtn}>▼ oppose</button>
                    <button onClick={() => resolveCh(c.challenge, "upheld")}
                            style={S.miniBtn}>✓ uphold (admin)</button>
                    <button onClick={() => resolveCh(c.challenge, "rejected")}
                            style={S.miniBtn}>✗ reject (admin)</button>
                  </>)}
                </div>))}
            </div>
          )}
          {tab === "Changes" && (
            <div>
              <h3 style={{ margin: "0 0 4px" }}>Removed from view</h3>
              <p style={{ opacity: 0.6, fontSize: 12.5, marginTop: 0 }}>
                The public record (ADR-0047): nothing is ever deleted from the
                log — these are hidden from the map, on the books forever.</p>
              {dels.length === 0 && <p style={{ opacity: 0.5 }}>Nothing removed.</p>}
              {dels.map((d) => (
                <div key={d.seq} style={S.reqBox}>
                  <b>{d.subject}</b>{" "}
                  <small style={{ opacity: 0.55 }}>{d.kind} · seq {d.seq}</small>
                  <div style={{ fontSize: 12.5, opacity: 0.75 }}>{d.reason}</div>
                  <div style={{ fontSize: 12, opacity: 0.55 }}>
                    marked by {d.marked_by ?? "?"} · approved by {d.approved_by}
                  </div>
                </div>))}
            </div>
          )}
          {!["Bounties", "Leaders", "Changes", "Tickets"].includes(tab)
            && !showAdd && !card &&
            <p style={{ opacity: 0.6 }}>Click a node — or search, upper
            right. Red ring = needs citation. Faded = nobody vouched yet.
            Everything builds from zero.</p>}
          {!["Bounties", "Leaders", "Changes", "Tickets"].includes(tab)
            && !showAdd && card && !card.missing && (
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
              <div style={{ margin: "10px 0" }}>
                <button onClick={() => setTool(tool === "link" ? null : "link")}
                        style={S.miniBtn}>+ link</button>
                <button onClick={openCite} style={S.miniBtn}>📖 cite</button>
                <button onClick={dispute} style={S.miniBtn}>⚑ dispute</button>
                <button onClick={markDelete} style={S.miniBtn}>🗑 delete</button>
              </div>
              {tool === "link" && (
                <div style={S.orBox}>
                  <div style={S.orTitle}>this node…</div>
                  <select value={link.rel} style={S.input}
                          onChange={(e) => setLink({ ...link, rel: e.target.value })}>
                    {Object.keys(REL).map((r) => <option key={r}>{r}</option>)}
                  </select>
                  <input placeholder="target node id (e.g. transistor)"
                         value={link.target} style={S.input}
                         onChange={(e) => setLink({ ...link, target: e.target.value })} />
                  <input placeholder="justification (why this link is true)"
                         value={link.just} style={S.input}
                         onChange={(e) => setLink({ ...link, just: e.target.value })} />
                  <input placeholder="year (optional)" value={link.year}
                         style={S.input}
                         onChange={(e) => setLink({ ...link, year: e.target.value })} />
                  <button onClick={submitLink} style={S.solveBtn}>Add link</button>
                </div>)}
              {tool === "cite" && fields && (
                <div style={S.orBox}>
                  <div style={S.orTitle}>cite / confirm a claim</div>
                  <select value={cite.aid} style={S.input}
                          onChange={(e) => setCite({ ...cite, aid: e.target.value })}>
                    <option value="">— pick the claim —</option>
                    {Object.entries(fields.fields ?? {}).map(([f, v]: any) => (
                      <option key={v.assertion} value={v.assertion}>
                        {f}: {String(v.value).slice(0, 40)}
                      </option>))}
                    {[...(card.requires ?? []), ...(card.enables ?? [])].map((e) => (
                      <option key={e.edge_id} value={e.edge_id}>
                        link ↔ {e.other_name}
                      </option>))}
                  </select>
                  <input placeholder="source (doc-id / URL / reference)"
                         value={cite.source} style={S.input}
                         onChange={(e) => setCite({ ...cite, source: e.target.value })} />
                  <input placeholder="locator (page, section — be precise)"
                         value={cite.locator} style={S.input}
                         onChange={(e) => setCite({ ...cite, locator: e.target.value })} />
                  <button onClick={submitCite} style={S.solveBtn}>Attach citation</button>
                  {cite.aid && !cite.aid.startsWith("e_") &&
                    <button onClick={() => confirmClaim(cite.aid)}
                            style={{ ...S.miniBtn, marginLeft: 6 }}>
                      ✓ I checked the source (L4)</button>}
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
