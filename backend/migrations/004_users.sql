-- The user database (user rulings 2026-08-09): identity ≠ credential ≠ score.
--   users        durable public identity — the HANDLE stamped into facts
--   credentials  disposable tokens: many per user, rotatable, revocable
-- Scores split by nature: INK (the gamified score — your ink on the record;
-- monotone up; deliberately NOT called karma) vs reputation (ADR-0013 trust:
-- earned by verified work, SLASHABLE). Everything public.
-- Agents REQUIRE an operator (accountability chain: blame rolls up to people).

CREATE TABLE IF NOT EXISTS users (
  user_id      TEXT PRIMARY KEY,          -- chosen handle; stamped into facts
  display_name TEXT,
  kind         TEXT NOT NULL CHECK (kind IN ('human','agent','system')),
  operator     TEXT REFERENCES users(user_id),  -- REQUIRED for agents
  bio          TEXT,
  link         TEXT,
  ink          INTEGER NOT NULL DEFAULT 0,
  reputation   INTEGER NOT NULL DEFAULT 0,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CHECK (kind <> 'agent' OR operator IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS credentials (
  token_hash      TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL REFERENCES users(user_id),
  budget_per_hour INTEGER NOT NULL DEFAULT 1000,
  created_at      timestamptz NOT NULL DEFAULT now(),
  revoked_at      timestamptz
);

-- migrate from the old identities table (humans first, then agents under
-- andrew), then drop it — guarded so the migration is rerunnable
DO $$ BEGIN
  IF EXISTS (SELECT FROM information_schema.tables
             WHERE table_name = 'identities') THEN
    INSERT INTO users (user_id, display_name, kind, ink)
      SELECT identity->>'id', identity->>'id', identity->>'type', points
      FROM identities WHERE identity->>'type' <> 'agent'
      ON CONFLICT DO NOTHING;
    INSERT INTO users (user_id, display_name, kind, operator, ink)
      SELECT identity->>'id', identity->>'id', 'agent', 'andrew', points
      FROM identities WHERE identity->>'type' = 'agent'
      ON CONFLICT DO NOTHING;
    INSERT INTO credentials (token_hash, user_id, budget_per_hour)
      SELECT token_hash, identity->>'id', budget_per_hour FROM identities
      ON CONFLICT DO NOTHING;
    DROP TABLE identities;
  END IF;
END $$;
