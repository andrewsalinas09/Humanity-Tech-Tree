"""Three-valued logic (ADR-0037): SAT / VIOL / UNKNOWN with Kleene composition.

Vacuity (H11: a pruned leaf/connective) is NOT a truth value — vacuous elements are
*removed* before composition; callers represent vacuity as Python None.
"""
from enum import Enum


class Tri(Enum):
    SAT = "SATISFIED"
    VIOL = "VIOLATED"
    UNKNOWN = "UNKNOWN"


def t_and(values):
    """Kleene AND: VIOL dominates; else UNKNOWN if any; else SAT. Empty AND is SAT
    (nothing demanded, nothing unmet — the implicit-AND-of-zero-edges magic-box case)."""
    vals = [v for v in values if v is not None]
    if any(v is Tri.VIOL for v in vals):
        return Tri.VIOL
    if any(v is Tri.UNKNOWN for v in vals):
        return Tri.UNKNOWN
    return Tri.SAT


def t_or(values):
    """Kleene OR: SAT dominates; else UNKNOWN if any; else VIOL.
    Empty OR (all branches vacuous) is vacuous — caller must treat as None (H11)."""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    if any(v is Tri.SAT for v in vals):
        return Tri.SAT
    if any(v is Tri.UNKNOWN for v in vals):
        return Tri.UNKNOWN
    return Tri.VIOL


def t_not(v):
    """Kleene NOT: swaps SAT/VIOL; UNKNOWN unchanged; vacuous stays vacuous."""
    if v is None:
        return None
    return {Tri.SAT: Tri.VIOL, Tri.VIOL: Tri.SAT, Tri.UNKNOWN: Tri.UNKNOWN}[v]


# Ordering for OR branch selection (best first): SAT > UNKNOWN > VIOL
RANK = {Tri.SAT: 2, Tri.UNKNOWN: 1, Tri.VIOL: 0}
