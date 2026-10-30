"""page_scores.py — оценки A–E по целям (/scores)."""
from html import escape as e


def _emps(data):
    return [x for x in (data.get("employees") or []) if isinstance(x, dict)]


def _period(data):
    try:
        import grading_compat as gc
        if getattr(gc, "PERIOD", None):
            return gc.PERIOD
    except Exception:
        pass
    return str(data.get("period") or "—")


def _goals_of(emp):
    try:
        import grading_compat as gc
        return gc._goals_for(emp) or []
    except Exception:
        pass
    gs = emp.get("goals")
    return gs if isinstance(gs, list) else []


def _pct(plan, fact):
    try:
        plan, fact = float(plan or 0), float(fact or 0)
    except (TypeError, ValueError):
        return None
    return None if plan <= 0 else round(fact * 100.0 / plan, 1)


def _weighted(goals):
    """Взвешенный % по config.GOAL_WEIGHTS (Ц1=0.4, Ц2=0.4, Ц3=0.2)."""
    pairs = []
    for g in goals:
        if isinstance(g, dict) and g.get("c"):
            v = _pct(g.get("plan"), g.get("fact"))
            if v is not None:
                pairs.append((g["c"], v))
    if not pairs:
        return None
    try:
        import config
        W = getattr(config, "GOAL_WEIGHTS", {}) or {}
    except Exception:
        W = {}
    if W and all(c in W for c, _ in pairs):
        tot = sum(W[c] for c, _ in pairs)
        return round(sum(W[c] * v for c, v in pairs) / tot, 1)
    n = 3 if len(pairs) >= 3 else len(pairs)
    return round(sum(v for _, v in pairs[:n]) / n, 1)


def _deploy(goals):
    """Статус внедрения — как у /team: приоритет in_use среди целей."""
    for g in goals:
        if isinstance(g, dict) and g.get("deploy") == "in_use":
            return "in_use"
    return "none"


def _letter(pct, deploy="none"):
    if pct is None:
        return "—"
    try:
        import grading
        return grading.letter_for(pct, deploy)
    except Exception:
        return "—"


def _cls(letter):
    if letter not in "ABCDE":
        return "muted"
    if letter in "AB":
        return "ok"
    if letter in "DE":
        return "risk"
    return "warn"


def _money(v):
    try:
        return format(int(v or 0), ",d").replace(",", "\u00a0") + " \u20bd"
    except (TypeError, ValueError):
        return "—"


def _cell(v):
    return '<td class="muted">—</td>' if v is None else "<td>" + str(v) + "%</td>"


def page_scores(data):
    rows, counts, ok_kpi = [], {}, 0
    for emp in _emps(data):
        goals = _goals_of(emp)
        by = {g["c"]: _pct(g.get("plan"), g.get("fact"))
              for g in goals if isinstance(g, dict) and g.get("c")}
        w = _weighted(goals)
        L = _letter(w, _deploy(goals))
        counts[L] = counts.get(L, 0) + 1
        if w is not None and w >= 100:
            ok_kpi += 1
        rows.append(
            "<tr><td><b>" + e(emp.get("name", "—")) + "</b></td><td>"
            + _money(emp.get("salary")) + "</td>"
            + _cell(by.get("Ц1")) + _cell(by.get("Ц2")) + _cell(by.get("Ц3"))
            + "<td><b>" + ("—" if w is None else str(w) + "%") + "</b></td>"
            + '<td><span class="badge ' + _cls(L) + '">' + L + "</span></td></tr>")
    if not rows:
        rows = ['<tr><td colspan="7" class="muted">Нет данных</td></tr>']
    counts_rows = "".join(
        "<tr><td><b>" + L + "</b></td><td>" + str(counts.get(L, 0)) + "</td></tr>"
        for L in "ABCDE")
    cards = ('<div class="grid">'
             '<div class="kpi"><span class="muted">Период</span><b>' + e(str(_period(data))) + "</b></div>"
             '<div class="kpi"><span class="muted">Сотрудников</span><b>' + str(len(_emps(data))) + "</b></div>"
             '<div class="kpi"><span class="muted">КПИ выполнены</span><b>' + str(ok_kpi) + "</b></div></div>")
    return ("<h2>Оценки по целям</h2>" + cards
            + "<h3>Буквы</h3>"
            '<div class="card wrap"><table><tr><th>Буква</th><th>Человек</th></tr>'
            + counts_rows + "</table></div>"
            "<h3>Детально</h3>"
            '<div class="card wrap"><table>'
            "<tr><th>Сотрудник</th><th>Оклад</th><th>Ц1</th><th>Ц2</th><th>Ц3</th>"
            "<th>Взвеш. %</th><th>Буква</th></tr>" + "".join(rows) + "</table></div>")
