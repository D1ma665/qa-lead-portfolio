"""grading_compat.py — слой совместимости для app.py.

app.py ожидает старый API grading:
    scores_for, grade_of, coverage, average, next_grade_gap, goal_breakdown

Здесь они реализованы через текущий grading.py (grade_with_fallback,
competencies_percent, active_goals и т.д.). Сам grading.py не изменяется.

Подключение в app.py:
    import grading_compat as grading   # вместо import grading
"""

import json
import os
import sys
import config
import grading

PERIOD = "2026-Q4"

# лестница грейдов: код -> (название, минимальная средняя)
LADDER = [
    ("J1", "Джун 1", 3.25),   # 65% от 5
    ("J2", "Джун 2", 3.75),   # 75%
    ("M3", "Мидл 3", 4.10),   # 82%
    ("M4", "Мидл 4", 4.50),   # 90%
    ("S5", "Сеньор 5", 4.80), # 96%
    ("S6", "Сеньор 6", 4.80), # максимум
]


def _period(emp):
    """Текущий период сотрудника (первый доступный, иначе PERIOD)."""
    per = (emp.get("scores") or {})
    if PERIOD in per:
        return PERIOD
    return next(iter(per), PERIOD)


def scores_for(emp):
    """{компетенция: балл} за текущий период."""
    if not isinstance(emp, dict):
        return {}
    row = (emp.get("scores") or {}).get(_period(emp)) or {}
    return dict(row)


def average(emp):
    """Средний балл по оценённым компетенциям (шкала 0..MAX_SCORE)."""
    row = scores_for(emp)
    vals = [v for v in row.values() if isinstance(v, (int, float))]
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 2)


def grade_of(emp):
    """(код, название грейда). Код берётся из LADDER, не из названия.

    Раньше здесь стоял early-return `not scores_for(emp)` -> ("",
    "нет грейда"), и code всегда приходил пустым. Из-за этого:
      * Якин (без оценок) показывал "нет грейда" (п. 6.5);
      * next_grade_gap уходил в ветку `if not code` и отдавал
        "-> J1 (0/1)" ВСЕМ 13, включая Сидорова с "Мидл 3" (п. 6.6, 6.7).
    """
    try:
        g = grading.grade_with_fallback(emp, _period(emp))
    except Exception as e:
        print(f"[grading_compat] grade_of: {e}", file=sys.stderr)
        return ("", "нет грейда")

    name = g.get("name") if isinstance(g, dict) else None
    if not name:
        return ("", "нет грейда")

    for code, gname, _min_avg in LADDER:
        if gname == name:
            return (code, name)

    return ("", name)


def coverage(emps):
    """Доля оценённых компетенций по команде, в процентах."""
    total = 0
    filled = 0
    names = [c[0] for c in config.COMPS]
    for e in emps or []:
        if not isinstance(e, dict):
            continue
        row = scores_for(e)
        total += len(names)
        filled += sum(1 for n in names if isinstance(row.get(n), (int, float)))
    if not total:
        return 0
    return round(filled * 100.0 / total, 1)


def _check(ok, text):
    return {"ok": bool(ok), "text": text}


def next_grade_gap(emp):
    """(код следующего грейда, checks) где checks = [{'ok': bool, 'text': str}]."""
    code, name = grade_of(emp)
    if not code:
        return ("J1", [_check(False, "профиль не заполнен")])

    codes = [c for c, _, _ in LADDER]
    try:
        idx = codes.index(code)
    except ValueError:
        return ("", [])

    if idx + 1 >= len(LADDER):
        return ("", [_check(True, "максимальный грейд")])

    nxt_code, nxt_name, min_avg = LADDER[idx + 1]
    avg = average(emp)
    row = scores_for(emp)
    checks = []

    if min_avg:
        checks.append(_check(avg >= min_avg,
                             "средняя {:.2f} / {:.2f}".format(avg, min_avg)))

    # Раньше стояло `if low:` — пройденный критерий исчезал из списка,
    # и Сидоров (20/20 п1 >= 3) показывал "0 из 1" (п. 6.9).
    # Счётчик п1: X/Y = из Y ОЦЕНЁННЫХ приоритетных X шт. >= 4.
    # Знаменатель - оценённые, а не все 20: полный профиль давал
    # ложное 20/20 (Якин), а "оценено всё" гасило счётчик у 12 из 13.
    # Неполнота анкеты - в отдельной проверке "не оценено N".
    p1 = [c[0] for c in config.COMPS if c[2] == 1]
    scored = [n for n in p1 if isinstance(row.get(n), (int, float))]
    low = [n for n in scored if row[n] < 3]   # порог 4 -> 3 (п. 6.29/6.32)
    if scored:
        checks.append(_check(len(low) == 0,
                             "п1 >= 3: {}/{}".format(len(scored) - len(low), len(scored))))
    else:
        checks.append(_check(False, "п1: оценок нет"))

    missing = [c[0] for c in config.COMPS
               if c[2] in (1, 2, 3) and not isinstance(row.get(c[0]), (int, float))]
    checks.append(_check(len(missing) == 0,
                         "не оценено {}".format(len(missing))))

    return (nxt_code, checks)


def _all_goals():
    """Цели всех сотрудников из state.json (фолбэк, если emp их не содержит).

    Путь строится от файла модуля: open("state.json") зависел от текущего
    каталога и вне app/ молча возвращал {} (п. 6.1).
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
        return (s.get("employee_goals") or {})
    except FileNotFoundError:
        print(f"[grading_compat] не найден {path}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"[grading_compat] ошибка чтения {path}: {e}", file=sys.stderr)
        return {}


_GOALS_CACHE = {"mtime": None, "data": {}}


def _goals_for(emp):
    """Цели сотрудника: сначала из emp, иначе из state.json."""
    g = (emp.get("goals") or {}).get(PERIOD)
    if g:
        return g
    name = emp.get("name")
    store = _all_goals().get(PERIOD) or {}
    return store.get(name) or []


def goal_breakdown(emp):
    """{код цели: "факт%"} за текущий период."""
    out = {}
    for g in _goals_for(emp):
        if not isinstance(g, dict):
            continue
        code = g.get("c", "?")
        plan = g.get("plan") or 0
        fact = g.get("fact")
        if fact is None:
            out[code] = "—"
        elif not plan:
            out[code] = "нет плана"
        else:
            pct = round(fact * 100.0 / plan, 1)
            right = " %" if pct == 100 else "%"
            out[code] = "{}{}".format(pct, right)
    return out
