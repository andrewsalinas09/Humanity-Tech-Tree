-- The linter is an identity (ADR-0046 kind='system'): when the graph files
-- bounties on itself (sibling clusters -> WANT_NODE requests), the requests
-- are authored and blameable like everything else.
INSERT INTO users (user_id, display_name, kind)
  VALUES ('linter', 'Structure Linter', 'system')
  ON CONFLICT DO NOTHING;
