import config
"""
grading.py — расчёт грейда и покрытия команды (Этап 1)

Грейд — «система планок»: максимальный уровень, все пороги которого
выполнены. Берутся только компетенции, входящие в оценку (есть балл 1–5).

Этап 1: НЕ считает A–E по целям и премию по целям.
"""

import config


def scores_for(emp, comps=None):
    """Баллы сотрудника по компетенциям в виде {название: балл}."""
    comps = comps or config.COMPS
    raw = emp.get("scores", {})
    return {name: raw[name] for name, *_ in comps if raw.get(name) not in (None, "")}


def by_priority(emp, prio, comps=None):
    """Список баллов сотрудника по компетенциям заданного приоритета."""
    comps = comps or config.COMPS
    sc = scores_for(emp, comps)
    return [sc[name] for name, _cat, p, _goal in comps if p == prio and name in sc]


def average(emp, comps=None):
    vals = list(scores_for(emp, comps).values())
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def grade_of(emp, comps=None):
    """
    Возвращает (code, name) максимального грейда, все планки которого выполнены.
    Если не проходит даже Джун 1 — ("none", "Ниже Джун 1").
    """
    comps = comps or config.COMPS
    avg = average(emp, comps)
    reached = ("none", "Ниже Джун 1")

    for code, name, p1, p2, p3, avg_min, p1_few in config.GRADES:
        ok = True
        if p1 is not None:
            v = by_priority(emp, 1, comps)
            ok = bool(v) and min(v) >= p1
        if ok and p2 is not None:
            v = by_priority(emp, 2, comps)
            ok = bool(v) and min(v) >= p2
        if ok and p3 is not None:
            v = by_priority(emp, 3, comps)
            ok = bool(v) and min(v) >= p3
        if ok and p1_few is not None:
            v = by_priority(emp, 1, comps)
            ok = sum(1 for x in v if x >= p1_few) >= 2
        if ok and avg_min is not None:
            ok = avg >= avg_min
        if ok:
            reached = (code, name)
    return reached


def next_grade_gap(emp, comps=None):
    """
    Что не хватает до следующего грейда.
    Возвращает список требований вида {'text': ..., 'ok': bool}.
    """
    code, _name = grade_of(emp, comps)
    codes = [g[0] for g in config.GRADES]
    idx = codes.index(code) + 1 if code in codes else 0
    if idx >= len(codes):
        return ("senior6", [])

    c, n, p1, p2, p3, avg_min, p1_few = config.GRADES[idx]
    comps = comps or config.COMPS
    checks = []

    def add_prio(prio, need):
        v = by_priority(emp, prio, comps)
        worst = min(v) if v else 0
        total = len(v)
        missing = sum(1 for x in v if x < need)
        tail = ", не хватает " + str(missing) if missing else ", все готовы"
        checks.append({
            "text": f"п{prio} ≥ {need} — все {total} компетенций {tail} (сейчас мин. {worst})",
            "ok": bool(v) and worst >= need,
        })

    if p1 is not None:
        add_prio(1, p1)
    if p2 is not None:
        add_prio(2, p2)
    if p3 is not None:
        add_prio(3, p3)
    if p1_few is not None:
        v = by_priority(emp, 1, comps)
        cnt = sum(1 for x in v if x >= p1_few)
        checks.append({"text": f"минимум 2 компетенции приоритета 1 на {p1_few}+ (сейчас {cnt})", "ok": cnt >= 2})
    if avg_min is not None:
        a = average(emp, comps)
        checks.append({"text": f"средняя ≥ {avg_min} (сейчас {a})", "ok": a >= avg_min})

    return (c, checks)


# ------------------------------------------------------ покрытие команды

def coverage(employees, comps=None, threshold=None):
    """
    Покрытие компетенций командой: кто владеет на уровне >= threshold.
    Для приоритета 1 важно, что владеют ВСЕ; для 2 — несколько; для 3 — один-два.
    """
    if threshold is None:
        threshold = config.COVERAGE_MIN
    comps = comps or config.COMPS
    total = len(employees)
    rows = []

    for name, cat, prio, goal in comps:
        owners = [e for e in employees if (e.get("scores", {}).get(name) or 0) >= threshold]
        n = len(owners)
        if prio == 1:
            need = total
            status = "ok" if n >= total else "risk"
        elif prio == 2:
            need = max(2, round(total * 0.3))
            status = "ok" if n >= need else "risk"
        else:
            need = 2
            status = "ok" if n >= need else ("risk" if n == 0 else "warn")
        rows.append({
            "comp": name, "cat": cat, "prio": prio, "goal": goal,
            "owners": [e.get("name") for e in owners],
            "count": n, "need": need, "total": total, "status": status,
        })
    return rows


def goal_breakdown(emp, comps=None):
    """
    Срез по целям: средний балл компетенций, привязанных к каждой цели.
    Только для просмотра (в Этапе 1 не влияет на A–E).
    """
    comps = comps or config.COMPS
    sc = scores_for(emp, comps)
    out = {}
    for g in config.GOALS:
        vals = [sc[n] for n, _c, _p, goal in comps if goal == g and n in sc]
        out[g] = round(sum(vals) / len(vals), 2) if vals else None
    return out
