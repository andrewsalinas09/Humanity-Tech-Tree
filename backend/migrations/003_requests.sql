-- Requests ("bounties"): the crowdsourcing loop (user rulings 2026-08-09).
-- A request is WORKFLOW, not a fact — it never enters the fact log.
-- Grounded in the arch's own wants (nothing invented):
--   WANT_NODE      a node that should exist (carries proposed name/description)
--   WANT_COVERAGE  an existing node's dependencies are incomplete (solver gaps)
--   WANT_EVIDENCE  claims on a subject need citations (the red-ring game)
-- offered_sources = citations-in-waiting, the arch's own {source, locator} shape.

CREATE TABLE IF NOT EXISTS requests (
  request_id        BIGSERIAL PRIMARY KEY,
  want              TEXT NOT NULL CHECK (want IN
                      ('WANT_NODE','WANT_COVERAGE','WANT_EVIDENCE')),
  subject_node      TEXT,             -- existing node (COVERAGE/EVIDENCE)
  wanted_name       TEXT,             -- WANT_NODE: what should exist
  wanted_description TEXT,
  notes             TEXT,
  offered_sources   JSONB NOT NULL DEFAULT '[]',  -- [{source, locator}]
  status            TEXT NOT NULL DEFAULT 'open', -- open | fulfilled
  requested_by      JSONB NOT NULL,
  fulfilled_by      JSONB,
  fulfilled_links   JSONB,            -- node/edge/assertion ids that satisfied it
  opened_at         timestamptz NOT NULL DEFAULT now(),
  fulfilled_at      timestamptz
);

-- Endorsements: identity-stamped votes; agents work the most-wanted first.
CREATE TABLE IF NOT EXISTS request_endorsements (
  request_id  BIGINT NOT NULL REFERENCES requests(request_id),
  endorser    TEXT NOT NULL,          -- identity id (server-stamped)
  endorsed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (request_id, endorser)
);

-- Karma (gamified prestige, user ruling): fulfilling earns points scaled by
-- endorsement; posting a later-fulfilled request earns a little too.
ALTER TABLE identities ADD COLUMN IF NOT EXISTS points INTEGER NOT NULL DEFAULT 0;
