from config import (GRADES, MARK_K, MARK_LABEL, PAUSE_QUARTERS,
                    RISK_QUARTERS, GOALS, HISTORY, BASES, PPL, COMPS, SCORES)


def comp_pct(scores_row):
    tw = 0.0
    acc = 0.0
    for i, c in enumerate(COMPS):
        if c[4] != chr(1044) + chr(1040):
            continue
        b = max(1, min(5, int(scores_row[i])))
        acc += ((b - 1) / 4 * 100) * c[3]
        tw += c[3]
    return round(acc / tw, 2) if tw else 0.0


def goal_ratio(person, goals):
    gs = [g for g in goals if g["person"] == person]
    return round(sum(g["pct"] for g in gs) / len(gs)) if gs else 0


def mark_from_goals(person, goals):
    gs = [g for g in goals if g["person"] == person]
    if not gs:
        return "E"
    r = goal_ratio(person, goals)
    over = any(g["over"] and g["pct"] >= 100 for g in gs)
    if over and r >= 100: return "A"
    if r >= 100: return "B"
    if r >= 60: return "C"
    if r >= 30: return "D"
    return "E"


def grade_idx(pct):
    idx = -1
    for i, g in enumerate(GRADES):
        if pct >= g[1]:
            idx = i
    return idx


def quarters_below(person, gidx, history):
    thr = GRADES[gidx][1] if gidx >= 0 else min(g[1] for g in GRADES)
    below = 0
    for h in reversed(history.get(person, [])):
        if h < thr:
            below += 1
        else:
            break
    return below


def discipline_state(below):
    if below >= RISK_QUARTERS: return "RISK"
    if below >= PAUSE_QUARTERS: return "PAUSE"
    if below >= 1: return "WARN"
    return "OK"


def build_results(people=None, history=None, bases=None, goals=None, scores=None):
    people = PPL if people is None else people
    history = HISTORY if history is None else history
    bases = BASES if bases is None else bases
    goals = GOALS if goals is None else goals
    scores = SCORES if scores is None else scores

    out = []
    for p in people:
        cur = comp_pct(scores.get(p, [1] * len(COMPS)))
        hist = history.get(p, [])
        last = hist[-1] if hist else cur
        best = max(hist) if hist else 0
        gi = grade_idx(cur)
        below = quarters_below(p, gi, history)
        st = discipline_state(below)
        mk = mark_from_goals(p, goals)
        r = goal_ratio(p, goals)
        gname = GRADES[gi][0] if gi >= 0 else "-"
        gpc = GRADES[gi][2] if gi >= 0 else 0.0
        prem = round(bases.get(p, 0) * gpc * MARK_K[mk])
        out.append({
            "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a": p,
            "% \u043a\u043e\u043c\u043f\u0435\u0442\u0435\u043d\u0446\u0438\u0439": cur,
            "\u0413\u0440\u0435\u0439\u0434": gname,
            "gidx": gi,
            "% \u043f\u0440\u0435\u043c\u0438\u0438": gpc,
            "% \u0446\u0435\u043b\u0438": r,
            "\u041e\u0446\u0435\u043d\u043a\u0430": mk,
            "\u0421\u043c\u044b\u0441\u043b": MARK_LABEL[mk],
            "\u041a\u043e\u044d\u0444.": MARK_K[mk],
            "\u041e\u043a\u043b\u0430\u0434": bases.get(p, 0),
            "\u041f\u0440\u0435\u043c\u0438\u044f": prem,
            "\u0421\u0442\u0430\u0442\u0443\u0441": st,
        })
    return out
