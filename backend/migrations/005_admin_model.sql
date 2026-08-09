-- Agent model provenance + admin flag (delete tickets are admin-approved,
-- user ruling 2026-08-09 resolving Q-23).

ALTER TABLE users ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
UPDATE users SET is_admin = TRUE WHERE user_id = 'andrew';
