"""Reputation: a pure function of the fact log (ADR-0049).

Never authored, never stale — computed over verification/challenge/vote event
facts; `users.reputation` is only a cache. All numbers are TUNABLE parameters.
"""

EARN_L3, EARN_L4, EARN_L5 = 1, 3, 5
EARN_VERIFY_STANDS = 1
EARN_CHALLENGE_UPHELD = 3
SLASH_DEMOTED = -1          # good-faith wrongness is cheap (user ruling)
SLASH_BAD_VOUCH = -2
SLASH_HALLUCINATED = -4
SLASH_VANDALISM = -25
OPERATOR_ROLLUP = 0.5       # fraction of an agent's slash its operator eats
L5_HUMANS = 2               # independent human confirms for L5
VESTING_CLAIMS = 3          # standing L3+ claims before votes count


def claim_levels(facts):
    """{assertion_id: level 1..5} + per-assertion author, from event facts."""
    authors, machine, humans, demoted = {}, set(), {}, set()
    for f in facts:
        b, k = f["body"], f["kind"]
        if k == "assert":
            authors[f["fact_id"]] = f["author"].get("id") if isinstance(f["author"], dict) else None
        elif k == "verification.machine" and b.get("verdict") == "supported":
            machine.add(b["assertion_id"])
        elif k == "verification.human":
            if b.get("verdict") == "supported":
                humans.setdefault(b["assertion_id"], set()).add(
                    f["author"].get("id") if isinstance(f["author"], dict) else None)
            else:
                demoted.add(b["assertion_id"])
        elif k == "challenge.resolve" and b.get("outcome") == "upheld":
            for d in b.get("demoted", []):
                demoted.add(d)
    levels = {}
    for aid, author in authors.items():
        if aid in demoted:
            levels[aid] = 1
        elif len(humans.get(aid, ())) >= L5_HUMANS:
            levels[aid] = 5
        elif humans.get(aid):
            levels[aid] = 4
        elif aid in machine:
            levels[aid] = 3
        else:
            levels[aid] = None            # 1 vs 2 needs citation info; not rep-relevant
    return levels, authors, demoted


def compute(facts, operators=None):
    """{user_id: reputation} over the whole log. operators: {agent: operator}.
    Earning keys on the highest rung a claim ever REACHED — demotion is only
    its flat slash, NEVER a clawback of earned rungs (user ruling)."""
    operators = operators or {}
    authors, machine, humans, demoted = {}, set(), {}, set()
    for f in facts:
        b, k = f["body"], f["kind"]
        if k == "assert":
            authors[f["fact_id"]] = (f["author"].get("id")
                                     if isinstance(f["author"], dict) else None)
        elif k == "verification.machine" and b.get("verdict") == "supported":
            machine.add(b["assertion_id"])
        elif k == "verification.human" and b.get("verdict") == "supported":
            humans.setdefault(b["assertion_id"], set()).add(
                f["author"].get("id") if isinstance(f["author"], dict) else None)
        elif k == "verification.human":
            demoted.add(b["assertion_id"])
        elif k == "challenge.resolve" and b.get("outcome") == "upheld":
            demoted.update(b.get("demoted", []))
    rep = {}

    def add(uid, pts):
        if uid:
            rep[uid] = rep.get(uid, 0) + pts
            if pts < 0 and uid in operators:      # slash rolls up (ADR-0049 §5)
                op = operators[uid]
                rep[op] = rep.get(op, 0) + pts * OPERATOR_ROLLUP

    for aid, author in authors.items():           # rungs REACHED, kept forever
        if aid in machine or humans.get(aid):
            add(author, EARN_L3)
        if humans.get(aid):
            add(author, EARN_L4)
        if len(humans.get(aid, ())) >= L5_HUMANS:
            add(author, EARN_L5)
    for aid in demoted:                           # gentle demotion slash
        add(authors.get(aid), SLASH_DEMOTED)

    for f in facts:
        b, k = f["body"], f["kind"]
        who = f["author"].get("id") if isinstance(f["author"], dict) else None
        if k in ("verification.machine", "verification.human"):
            target = b.get("assertion_id")
            if b.get("verdict") == "supported":
                if target in demoted:
                    add(who, SLASH_BAD_VOUCH)     # vouched, later found wrong
                else:
                    add(who, EARN_VERIFY_STANDS)
            elif b.get("verdict") == "hallucinated":
                add(authors.get(target), SLASH_HALLUCINATED)
        elif k == "challenge.resolve":
            if b.get("outcome") == "upheld":
                add(b.get("opened_by"), EARN_CHALLENGE_UPHELD)
        elif k == "moderation.vandalism":
            add(b.get("user"), SLASH_VANDALISM)
    return {u: round(r, 1) for u, r in rep.items()}


def vested(facts, user_id):
    """≥VESTING_CLAIMS standing L3+ claims ⇒ votes count (ADR-0049 §4)."""
    levels, authors, _ = claim_levels(facts)
    n = sum(1 for aid, lvl in levels.items()
            if authors.get(aid) == user_id and lvl and lvl >= 3)
    return n >= VESTING_CLAIMS
