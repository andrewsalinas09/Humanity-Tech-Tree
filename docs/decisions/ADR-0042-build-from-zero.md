# ADR-0042: Build from zero — no field ever defaults to standing

- **Status:** Accepted
- **Date:** 2026-08-08
- **Source:** user ruling ("everything defaults to the unknown / uncertified / un-whatever thing. It has to build up from 0, always")

## Context
Defaults are silent claims. The old schema defaulted edge epistemic status to MAINSTREAM_FACT — an unassessed claim wearing a credibility badge at birth; the kernel's solver quietly defaulted missing validity to current_truth. Same bug shape as presumed-satisfiable (ADR-0037): absence of assessment leaking into positive standing.

## Decision
1. **No stored default ever confers standing.** Absent epistemic assessment → computed "**unassessed**" label (sibling of the red citation badge). Absent validity → the solver treats existence as UNKNOWN with a "validity unassessed" gap — never current_truth by fallback. Absent constraint data → UNKNOWN (ADR-0037). Absent citations → red (ADR-0030). Level starts at L1 (ADR-0032). Reputation starts at zero (ADR-0013).
2. **Standing is only ever an explicit, provenanced fact** (someone asserted validity; someone assessed epistemic status; someone cited, verified, vouched) — every rung of every ladder climbed from zero, on the record.
3. **Q1 companion (creation ergonomics):** creation verbs accept the initial conditions as optional kwargs — dates, epistemic, qualifier, justification — compiling ONE atomic ChangeRequest, so an edge can be *born complete* (the fringe claim born FRINGE; the 2010 camera edge born dated) instead of passing through a sloppy bare state. What isn't stated at birth simply starts at zero, honestly labeled.
4. **Justification: never required, always encouraged** (Q3 ruling) — a kwarg on every verb, demanded only where the law already demands it (L3 person links, exclusions, PHYSICAL constraints via citation), encouraged via tool instructions rather than per-call nagging.

## The blame corollary (user, same day)
"If an agent/person didn't personally vouch for the info, it's not there. We assign blame to people, not defaults." Every unit of standing must trace to an identity who explicitly asserted it and can be credited or slashed for it (ADR-0013 reputation, ADR-0029 provenance, ADR-0041 stamping). Consequences:
- **Default parameters are defaults in disguise**: a verb signature that fills in `validity="current_truth"` makes the caller vouch without deciding — inadmissible. Public-surface verbs take `validity=None` etc.; unstated stays absent.
- **Verb-compiled derived facts** (alias unions, expression rewrites, lifted edges) are owned by the invoking identity — you called the compiler, you own its output.
- **Decision resolutions** are owned by the resolver (`resolved_by`).
- The audit question "who said this?" has a non-empty answer for every fact, forever — no fact's provenance ever resolves to "the system assumed."

## Why
At swarm scale, defaults multiply by millions: a credibility default is a credibility *printing press*. Build-from-zero makes the graph's entire trust surface monotone-honest — everything starts as visibly unestablished and climbs only by recorded acts, which is also exactly what makes the "watch it ripen from red to green" experience true rather than cosmetic.

## Consequences
- Kernel: missing validity → existence capped UNKNOWN with gap (fallback removed).
- Verbs: initial-condition kwargs on creation verbs (start/end/epistemic/justification); `refine`/`succeed`/`associate` implemented.
- SCHEMA: edge `truth_level` absent = computed "unassessed"; no enum default.
