# grading.py — ЛОГИКА: грейд, оценка A-E, премия, дисциплина
# ---------------------------------------------------------------
from config import (GRADES, MARK_K, MARK_LABEL, PAUSE_QUARTERS,
                    RISK_QUARTERS, GOALS, HISTORY, BASES, PPL)


def grade_idx(pct):
    """Индекс грейда по проценту. -1 если ниже самого низкого порога."""
    idx = -1
    for i, (_, threshold, _) in enumerate(GRADES):
        if pct >= threshold:
            idx = i
    return idx


def grade_name(i):
    return GRADES[i][0] if i >= 0 else "—"


def grade_pc(i):
    return GRADES[i][2] if i >= 0 else 0.0


def goals_of(person):
    return [g for g in GOALS if g["person"] == person]


def goal_ratio(person):
    gs = goals_of(person)
    return round(sum(g["pct"] for g in gs) / len(gs)) if gs else 0


def mark_from_goals(person):
    gs = goals_of(person)
    if not gs:
        return "E"
    ratio = goal_ratio(person)
    over = any(g["over"] for g in gs)
    if over and ratio >= 100: return "A"
    if ratio >= 100:          return "B"
    if ratio >= 60:           return "C"
    if ratio >= 30:           return "D"
    return "E"


def quarters_below(person, gidx):
    threshold = GRADES[gidx][1] if gidx >= 0 else GRADES[0][1]
    below = 0
    for h in reversed(HISTORY.get(person, [])):
        if h < threshold:
            below += 1
        else:
            break
    return below


def discipline_state(below):
    if below >= RISK_QUARTERS:  return "Зона риска"
    if below >= PAUSE_QUARTERS: return "Приостановка"
    if below >= 1:              return "Внимание"
    return "Норма"


def build_results(people=None, history=None, bases=None):
    """Собирает итоговую таблицу. Можно передать изменённые данные из UI."""
    people = people or PPL
    history = history or HISTORY
    bases = bases or BASES
    results = []
    for person in people:
        hist = history.get(person, [])
        pct = hist[-1] if hist else 0
        best = max(hist) if hist else 0
        gidx = grade_idx(best)
        below = quarters_below(person, gidx)
        state = discipline_state(below)
        mk = mark_from_goals(person)
        ratio = goal_ratio(person)
        prem = round(bases.get(person, 0) * grade_pc(gidx) * MARK_K[mk])
        results.append({
            "Сотрудник": person,
            "% грейд": pct,
            "Грейд": grade_name(gidx),
            "gidx": gidx,
            "% премии": grade_pc(gidx),
            "% цели": ratio,
            "Оценка": mk,
            "Смысл": MARK_LABEL[mk],
            "Коэф.": MARK_K[mk],
            "Оклад": bases.get(person, 0),
            "Премия": prem,
            "Статус": state,
            "Рост": "Заблокирован" if below >= PAUSE_QUARTERS else "Открыт",
        })
    return results
