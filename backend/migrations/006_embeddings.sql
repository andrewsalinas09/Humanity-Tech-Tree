-- Semantic existence gate (ADR-0048, resolves Q-20): node embeddings.
-- Vectors are DERIVED data (ADR-0026) — rebuildable from name+aliases+
-- description at any time, so the model/provider is swappable forever.
-- Dev-scale storage: JSONB vec + Python KNN; production upgrade path is
-- pgvector/HNSW (container swap + reindex, no contract change).

CREATE TABLE IF NOT EXISTS embeddings (
  node_id   TEXT NOT NULL,
  model     TEXT NOT NULL,
  text_hash TEXT NOT NULL,          -- re-embed only when the text changed
  dim       INTEGER NOT NULL,
  vec       JSONB NOT NULL,
  updated   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (node_id, model)
);
