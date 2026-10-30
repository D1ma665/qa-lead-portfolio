"""comps.py — доступность компетенций по грейду и расчёт балла.

Правило (из обсуждения):
  * у компетенции есть минимальный уровень доступности (поле 2 в config.COMPS);
  * у грейда есть уровень (GRADE_LEVEL);
  * компетенция доступна, если min_level <= level(grade);
  * если недоступная компетенция уже оценена — оценка СОХРАНЯЕТСЯ,
    но в расчёт текущего грейда НЕ идёт ("ждёт своего грейда");
  * балл считается только по доступным оценённым компетенциям.
"""

import config


def grade_level(grade):
    """Уровень грейда 1..3. None -> 0 (ничего не доступно)."""
    if not grade:
        return 0
    return config.GRADE_LEVEL.get(grade, 0)


def comp_level(comp):
    """Минимальный уровень грейда для компетенции (поле 2)."""
    return comp[2]


def comp_name(comp):
    return comp[0]


def available_comps(grade):
    """Список компетенций, доступных на грейде."""
    lvl = grade_level(grade)
    return [c for c in config.COMPS if comp_level(c) <= lvl]


def split_scores(scores, grade):
    """Разделяет оценки на три корзины.

    Возвращает dict:
      available — доступные и оценённые: [(name, value)]
      reserved  — недоступные, но оценённые ("в запасе"): [(name, value, min_level)]
      missing   — доступные, но без оценки: [name]
    """
    lvl = grade_level(grade)
    row = scores or {}

    available, reserved, missing = [], [], []

    for c in config.COMPS:
        name, min_lvl = c[0], c[2]
        val = row.get(name)
        has = isinstance(val, (int, float))

        if min_lvl <= lvl:
            if has:
                available.append((name, val))
            else:
                missing.append(name)
        else:
            if has:
                reserved.append((name, val, min_lvl))

    return {"available": available, "reserved": reserved, "missing": missing}


def percent_of(pairs):
    """Средний балл по парам (name, value) в % от MAX_SCORE."""
    vals = [v for _, v in pairs]
    if not vals:
        return None
    return round(sum(vals) / (len(vals) * config.MAX_SCORE) * 100, 1)


def competency_percent(scores, grade):
    """Балл по доступным компетенциям. None, если грейд не задан или нет оценок."""
    if not grade:
        return None
    parts = split_scores(scores, grade)
    return percent_of(parts["available"])


def reserved_percent(scores, grade):
    """Балл по 'запасённым' компетенциям — что зачтётся при повышении."""
    parts = split_scores(scores, grade)
    return percent_of([(n, v) for n, v, _ in parts["reserved"]])


def next_grade(grade):
    """Следующий грейд по лестнице или None, если уже последний."""
    grades = [g[0] for g in config.GRADES]
    if grade not in grades:
        return None
    i = grades.index(grade)
    return grades[i + 1] if i + 1 < len(grades) else None


def readiness(scores, grade):
    """Готовность к следующему грейду.

    Считает:
      current_level / next_level
      unlocked      — компетенции, которые откроются при повышении: [(name, min_level)]
      already_have  — из них уже оценённые: [(name, value)]
      fill_pct      — доля 'запасённых' среди всех открывающихся, %
    """
    cur_lvl = grade_level(grade)
    nxt = next_grade(grade)
    nxt_lvl = grade_level(nxt) if nxt else cur_lvl

    row = scores or {}
    unlocked = [c for c in config.COMPS if cur_lvl < c[2] <= nxt_lvl]
    already = [(c[0], row[c[0]]) for c in unlocked
               if isinstance(row.get(c[0]), (int, float))]

    return {
        "current": grade,
        "current_level": cur_lvl,
        "next": nxt,
        "next_level": nxt_lvl,
        "levels_up": nxt_lvl > cur_lvl,
        "unlocked": [(c[0], c[2]) for c in unlocked],
        "already_have": already,
        "fill_pct": round(len(already) / len(unlocked) * 100, 1) if unlocked else None,
    }


def report(scores, grade):
    """Человекочитаемая раскладка для одного сотрудника."""
    parts = split_scores(scores, grade)
    return {
        "grade": grade,
        "level": grade_level(grade),
        "available_total": len(available_comps(grade)),
        "available_scored": len(parts["available"]),
        "missing": parts["missing"],
        "percent": percent_of(parts["available"]),
        "reserved": parts["reserved"],
        "reserved_percent": percent_of([(n, v) for n, v, _ in parts["reserved"]]),
        "readiness": readiness(scores, grade),
    }
