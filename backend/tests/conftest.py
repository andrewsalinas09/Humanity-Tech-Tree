"""Tests get their OWN database — never the live graph.

test_service's fixture wipes whatever database it is pointed at; before this
file existed it pointed at the live one (and once deadlocked mid-wipe against
the running tiler). Now HTT_PG_DSN is forced to httk_test for every test in
this suite, and the database is created on first run.
"""
import os

import psycopg

_ADMIN = os.environ.get("HTT_PG_ADMIN_DSN",
                        "postgresql://postgres:httk@localhost:5433/postgres")
_TEST_DSN = os.environ.get("HTT_PG_TEST_DSN",
                           "postgresql://postgres:httk@localhost:5433/httk_test")

os.environ["HTT_PG_DSN"] = _TEST_DSN


def pytest_configure(config):
    try:
        with psycopg.connect(_ADMIN, autocommit=True) as conn:
            got = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname='httk_test'").fetchone()
            if not got:
                conn.execute("CREATE DATABASE httk_test")
    except Exception:
        pass                      # no postgres → DB tests skip themselves
