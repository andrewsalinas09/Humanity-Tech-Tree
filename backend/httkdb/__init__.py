"""Postgres fact-log storage (SCHEMA.md §8-9). The log is the truth; tables are indexes."""
from .factlog import PgFactLog, ChangeRequest

__all__ = ["PgFactLog", "ChangeRequest"]
