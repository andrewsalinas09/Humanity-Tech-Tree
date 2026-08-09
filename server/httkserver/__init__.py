"""The verb service (ADR-0040/0041): transport-agnostic core wrapped by stdio and HTTP MCP."""
import os as _os
import sys as _sys

_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
for _p in (_os.path.join(_root, "kernel"), _os.path.join(_root, "backend")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from .service import Service, AuthError, BudgetExceeded  # noqa: E402

__all__ = ["Service", "AuthError", "BudgetExceeded"]
