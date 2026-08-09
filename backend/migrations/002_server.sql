-- Server spine (ADR-0041): identity, budgets, decision tickets, search receipts.

-- Wall-clock on facts for budget windows (record time stays the seq logical clock).
ALTER TABLE facts ADD COLUMN IF NOT EXISTS wall_time timestamptz NOT NULL DEFAULT now();

-- Identity: token hash -> who. The SERVER stamps authors; callers are never trusted.
CREATE TABLE IF NOT EXISTS identities (
  token_hash      TEXT PRIMARY KEY,
  identity        JSONB NOT NULL,           -- {type: human|agent, id, model?, version?}
  budget_per_hour INTEGER NOT NULL DEFAULT 1000,
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- Decisions persisted as tickets (ADR-0041 §3): the check-queue substrate.
CREATE TABLE IF NOT EXISTS decision_tickets (
  ticket_id   BIGSERIAL PRIMARY KEY,
  verb        TEXT NOT NULL,
  params      JSONB NOT NULL,
  reason      TEXT NOT NULL,
  options     JSONB NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open',  -- open | resolved | cancelled
  opened_by   JSONB NOT NULL,
  resolved_by JSONB,
  choice      JSONB,
  opened_at   timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

-- Search receipts: the unskippable existence gate (Q-20 v1: deterministic).
CREATE TABLE IF NOT EXISTS search_receipts (
  receipt_id BIGSERIAL PRIMARY KEY,
  query      TEXT NOT NULL,
  results    JSONB NOT NULL,
  issued_to  JSONB NOT NULL,
  issued_at  timestamptz NOT NULL DEFAULT now()
);
