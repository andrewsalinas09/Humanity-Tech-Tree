"""The semantic lane of the existence gate (ADR-0048, resolves Q-20).

Two providers (user ruling: both): LOCAL (fastembed/BGE-small — free, offline,
always available) and API (any OpenAI-compatible endpoint when HTT_EMBED_API_KEY
is set). Embedding text = name + aliases + description — the reason description
is a first-class field (user: "indispensable for semantic search").
Vectors are derived data: rebuildable, model swappable, never truth.
"""
import hashlib
import json
import os

from psycopg.types.json import Jsonb

LOCAL_MODEL = "BAAI/bge-small-en-v1.5"
API_MODEL = os.environ.get("HTT_EMBED_API_MODEL", "text-embedding-3-small")
API_URL = os.environ.get("HTT_EMBED_API_URL",
                         "https://api.openai.com/v1/embeddings")

_local = None


def provider():
    """API when a key is configured (user ruling: both lanes), else local."""
    return "api" if os.environ.get("HTT_EMBED_API_KEY") else "local"


def model_name():
    return API_MODEL if provider() == "api" else LOCAL_MODEL


def _embed(texts):
    if provider() == "api":
        import httpx
        r = httpx.post(API_URL, timeout=60,
                       headers={"Authorization":
                                f"Bearer {os.environ['HTT_EMBED_API_KEY']}"},
                       json={"model": API_MODEL, "input": texts})
        r.raise_for_status()
        return [d["embedding"] for d in r.json()["data"]]
    global _local
    if _local is None:
        from fastembed import TextEmbedding
        _local = TextEmbedding(LOCAL_MODEL)
    return [list(map(float, v)) for v in _local.embed(texts)]


def _node_text(view, n):
    parts = [view.field(n, "name") or n]
    parts += [str(a) for a in (view.field(n, "aliases", []) or [])]
    nd = view.node(n) or {}
    parts.append(nd.get("category", ""))
    desc = view.field(n, "description")
    if desc:
        parts.append(desc)
    return " — ".join(p for p in parts if p)


def refresh(pg, view):
    """Embed new/changed nodes (text-hash gated — cheap when nothing moved)."""
    mdl = model_name()
    nodes = view.nodes()
    texts = {n: _node_text(view, n) for n in nodes}
    hashes = {n: hashlib.sha256(t.encode()).hexdigest() for n, t in texts.items()}
    with pg.conn.cursor() as c:
        c.execute("SELECT node_id, text_hash FROM embeddings WHERE model=%s", (mdl,))
        have = dict(c.fetchall())
    stale = [n for n in nodes if have.get(n) != hashes[n]]
    if not stale:
        return 0
    vecs = _embed([texts[n] for n in stale])
    with pg.conn.cursor() as c:
        for n, v in zip(stale, vecs):
            c.execute(
                "INSERT INTO embeddings (node_id, model, text_hash, dim, vec) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (node_id, model) DO UPDATE "
                "SET text_hash=EXCLUDED.text_hash, dim=EXCLUDED.dim, "
                "vec=EXCLUDED.vec, updated=now()",
                (n, mdl, hashes[n], len(v), Jsonb(v)))
        gone = [n for n in have if n not in set(nodes)]
        if gone:
            c.execute("DELETE FROM embeddings WHERE model=%s AND node_id = ANY(%s)",
                      (mdl, gone))
    return len(stale)


def semantic_search(pg, view, query, k=8, floor=0.35):
    """Top-k nearest nodes by cosine over the embedding space. Python KNN —
    fine to ~10^4; the pgvector/HNSW upgrade is storage-only (ADR-0048)."""
    mdl = model_name()
    qv = _embed([query])[0]
    with pg.conn.cursor() as c:
        c.execute("SELECT node_id, vec FROM embeddings WHERE model=%s", (mdl,))
        rows = c.fetchall()
    import math
    qn = math.sqrt(sum(x * x for x in qv)) or 1.0
    scored = []
    for n, vec in rows:
        v = vec if isinstance(vec, list) else json.loads(vec)
        dot = sum(a * b for a, b in zip(qv, v))
        vn = math.sqrt(sum(x * x for x in v)) or 1.0
        s = dot / (qn * vn)
        if s >= floor and view.node(n):
            scored.append((s, n))
    scored.sort(reverse=True)
    return [{"node_id": n, "score": round(s, 3),
             "name": view.field(n, "name") or n,
             "category": (view.node(n) or {}).get("category"),
             "description": view.field(n, "description")}
            for s, n in scored[:k]]
