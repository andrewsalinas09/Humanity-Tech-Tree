-- Reputation carries fractions (operator roll-up is 0.5x an agent's slash,
-- ADR-0049 §5) — an INTEGER column silently rounds the ledger.
ALTER TABLE users ALTER COLUMN reputation TYPE NUMERIC(10,2);
