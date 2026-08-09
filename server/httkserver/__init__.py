"""The verb service (ADR-0040/0041): transport-agnostic core wrapped by stdio and HTTP MCP."""
from .service import Service, AuthError, BudgetExceeded

__all__ = ["Service", "AuthError", "BudgetExceeded"]
