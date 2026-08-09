-- The gap economy (ADR-0051): missing texture auto-becomes bounties.
ALTER TABLE requests DROP CONSTRAINT IF EXISTS requests_want_check;
ALTER TABLE requests ADD CONSTRAINT requests_want_check CHECK (want IN
  ('WANT_NODE','WANT_COVERAGE','WANT_EVIDENCE','WANT_DESCRIPTION'));
