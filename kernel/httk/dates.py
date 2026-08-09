"""Decimal-year intervals with certain-violation-only comparison (H2 + ADR-0037).

A DatePoint {year, uncertainty} is the interval [year-u, year+u]. Temporal checks
return VIOL only when intervals are disjoint in the violating direction; overlap is
UNKNOWN (ADR-0037 supersedes H2's 'overlap passes' with the honest value); certainly
inside is SAT.
"""
from .tri import Tri


class Interval:
    def __init__(self, year, unc=0.0):
        self.lo, self.hi = year - unc, year + unc

    def __repr__(self):
        return f"[{self.lo}, {self.hi}]"


def cmp_certain(a_before, b_after):
    """Is interval a certainly <= interval b? SAT if a.hi <= b.lo (certainly ordered),
    VIOL if a.lo > b.hi (certainly violated), else UNKNOWN (overlap)."""
    if a_before.hi <= b_after.lo:
        return Tri.SAT
    if a_before.lo > b_after.hi:
        return Tri.VIOL
    return Tri.UNKNOWN


def point_in_span(year, start, end):
    """Is scalar query-year within [start, end] (either bound optional Interval)?
    Certain-violation semantics: VIOL only if certainly outside; UNKNOWN on overlap."""
    if start is not None:
        if year < start.lo:
            return Tri.VIOL
        if year < start.hi:
            return Tri.UNKNOWN
    if end is not None:
        if year > end.hi:
            return Tri.VIOL
        if year > end.lo:
            return Tri.UNKNOWN
    return Tri.SAT
