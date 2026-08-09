-- Humanity Tech Tree — storage v1 (SCHEMA.md §8, ADR-0031/0038).
-- THE LOG IS THE TRUTH: `facts` is append-only; every other table is a
-- rebuildable projection (an index over the log).

CREATE TABLE IF NOT EXISTS facts (
  seq       BIGSERIAL PRIMARY KEY,          -- record time: monotone logical clock (ADR-0034)
  fact_id   TEXT UNIQUE NOT NULL,
  kind      TEXT NOT NULL,                  -- node.create | edge.create | assert | retract | cite
  author    JSONB NOT NULL,                 -- {type: human|agent, id, model?, version?} (ADR-0029)
  cr_id     TEXT,
  body      JSONB NOT NULL
);

-- ============ projections (rebuildable from facts; never authoritative) ======

CREATE TABLE IF NOT EXISTS node_identities (
  node_id     TEXT PRIMARY KEY,
  category    TEXT NOT NULL,
  created_seq BIGINT NOT NULL
);

-- Edge identities: from/to/type immutable (ADR-0038); physically partitioned by
-- the 8-type basis — ADR-0024's partition key becomes the storage layout.
CREATE TABLE IF NOT EXISTS edge_identities (
  edge_id     TEXT NOT NULL,
  from_node   TEXT NOT NULL,
  to_node     TEXT NOT NULL,
  type        TEXT NOT NULL,
  qualifier   TEXT,
  created_seq BIGINT NOT NULL,
  PRIMARY KEY (edge_id, type)
) PARTITION BY LIST (type);

CREATE TABLE IF NOT EXISTS edges_enables         PARTITION OF edge_identities FOR VALUES IN ('ENABLES');
CREATE TABLE IF NOT EXISTS edges_component       PARTITION OF edge_identities FOR VALUES IN ('IS_COMPONENT_OF');
CREATE TABLE IF NOT EXISTS edges_ingredient      PARTITION OF edge_identities FOR VALUES IN ('IS_INGREDIENT_OF');
CREATE TABLE IF NOT EXISTS edges_type_of         PARTITION OF edge_identities FOR VALUES IN ('IS_TYPE_OF');
CREATE TABLE IF NOT EXISTS edges_refinement      PARTITION OF edge_identities FOR VALUES IN ('IS_REFINEMENT_OF');
CREATE TABLE IF NOT EXISTS edges_optimizes       PARTITION OF edge_identities FOR VALUES IN ('OPTIMIZES');
CREATE TABLE IF NOT EXISTS edges_succeeds        PARTITION OF edge_identities FOR VALUES IN ('SUCCEEDS');
CREATE TABLE IF NOT EXISTS edges_association     PARTITION OF edge_identities FOR VALUES IN ('ASSOCIATION');

CREATE INDEX IF NOT EXISTS idx_edges_from ON edge_identities (from_node);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON edge_identities (to_node);
CREATE INDEX IF NOT EXISTS idx_edges_qual ON edge_identities (qualifier);

-- Latest authoritative assertion per (subject, field) — as-of queries replay facts.
CREATE TABLE IF NOT EXISTS current_fields (
  subject_id        TEXT NOT NULL,
  field_path        TEXT NOT NULL,
  value             JSONB,
  assertion_fact_id TEXT NOT NULL,           -- what evidence targets (ADR-0038)
  seq               BIGINT NOT NULL,
  PRIMARY KEY (subject_id, field_path)
);

CREATE TABLE IF NOT EXISTS change_requests (
  cr_id       TEXT PRIMARY KEY,
  proposer    JSONB NOT NULL,
  status      TEXT NOT NULL DEFAULT 'draft', -- draft | merged | flagged
  flags       JSONB NOT NULL DEFAULT '[]',   -- H9 post-merge breaker findings
  created_seq BIGINT,
  merged_seq  BIGINT
);

-- Evidence targets ASSERTIONS, never bare nodes (ADR-0030/0038); locator per user ruling.
CREATE TABLE IF NOT EXISTS citations (
  citation_id        BIGSERIAL PRIMARY KEY,
  claim_assertion_id TEXT NOT NULL,
  source_node        TEXT NOT NULL,
  locator            TEXT,
  seq                BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_citations_claim ON citations (claim_assertion_id);
