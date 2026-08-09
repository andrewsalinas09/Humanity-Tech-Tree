-- Tickets must SHOW their evidence (user: "I have no idea what I'm hoisting").
ALTER TABLE decision_tickets ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '{}';
