-- Peak reputation (user 2026-08-09): the high-water mark is part of the
-- record — "was at 40, slashed to 10" tells a story current-only hides.
ALTER TABLE users ADD COLUMN IF NOT EXISTS max_reputation NUMERIC(10,2) NOT NULL DEFAULT 0;
UPDATE users SET max_reputation = GREATEST(max_reputation, reputation);
