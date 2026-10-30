"""grading.py — расчёт оценки за период: взвешенное среднее -> буква -> премия.

Правила (requirements-v2.3):
  * Цели с status != "done" не участвуют в расчёте (иначе всё станет E).
  * Веса: три цели -> 1/3 каждая, две -> 50/50, одна -> 100%.
  * Взвешенное среднее = Σ(fact / plan * 100 × weight).
  * Буква:  <50 E | <70 D | <100 C | >=100 B ; A = B + deploy == "in_use"
  * Коэффициент: config.MARK_K[буква]
  * Премия = оклад × BONUS_BASE_RATE × (1 + доля_грейда) × коэффициент

Грейд — с фолбэком на предыдущий период:
  * есть оценки за период             -> грейд по ним;
  * нет, но были раньше               -> грейд по последнему периоду с оценками;
  * нет никогда                       -> Джун 1 + grade_source="default".

Никакого ввода-вывода: только функции над данными.
"""

import config


# ---------------------------------------------------------------- цели

def active_goals(goals):
    """Только закрытые цели периода."""
    return [g for g in (goals or []) if g.get("status") == "done"]


def goal_completion(goal):
    """Выполнение одной цели в процентах (0..∞)."""
    plan = goal.get("plan") or 0
    fact = goal.get("fact") or 0
    if plan <= 0:
        return 0.0
    return fact / plan * 100.0


def weights_for(goals):
    """Веса по фактическому числу участвующих целей."""
    ids = [g.get("c") for g in goals if g.get("c") in config.GOAL_IDS]
    if len(ids) >= 3:
        return {gid: config.GOAL_WEIGHTS[gid] for gid in ids}
    if len(ids) == 2:
        return {gid: config.GOAL_WEIGHTS_TWO[gid] for gid in ids}
    if len(ids) == 1:
        return {ids[0]: 1.0}
    return {}


def weighted_percent(goals):
    """Взвешенное среднее по закрытым целям. None, если считать нечего."""
    done = active_goals(goals)
    if not done:
        return None
    w = weights_for(done)
    total = 0.0
    for g in done:
        gid = g.get("c")
        if gid not in w:
            continue
        total += goal_completion(g) * w[gid]
    return round(total, 1)


# ---------------------------------------------------------------- буква

def letter_for(percent, deploy="none"):
    """Буква A–E по взвешенному проценту и статусу внедрения."""
    if percent is None:
        return None
    if percent < config.LETTER_E_MAX:
        return "E"
    if percent < config.LETTER_D_MAX:
        return "D"
    if percent < config.LETTER_C_MAX:
        return "C"
    return "A" if deploy == "in_use" else "B"


def deploy_from_tasks(goal):
    """Статус внедрения выводится из бинарных задач-критериев."""
    tasks = goal.get("tasks") or []
    if not tasks:
        return "none"
    deploy_tasks = [t for t in tasks if t.get("kind") == "deploy"]
    usage_tasks = [t for t in tasks if t.get("kind") == "usage"]
    if not deploy_tasks or not all(t.get("done") for t in deploy_tasks):
        return "none"
    if usage_tasks and all(t.get("done") for t in usage_tasks):
        return "in_use"
    return "deployed"


def overall_deploy(goals):
    """Если целей несколько — берём лучший статус внедрения."""
    order = list(config.DEPLOY_STATUSES)
    best = "none"
    for g in active_goals(goals):
        st = g.get("deploy") or deploy_from_tasks(g)
        if st not in order:          # неизвестный статус не роняет расчёт
            continue
        if order.index(st) > order.index(best):
            best = st
    return best


# ---------------------------------------------------------------- компетенции

def scores_percent(emp, period):
    """Средний балл компетенций за период в %. None, если оценок нет."""
    row = ((emp or {}).get("scores") or {}).get(period) or {}
    vals = [v for v in row.values() if isinstance(v, (int, float))]
    if not vals:
        return None
    return round(sum(vals) / (len(vals) * config.MAX_SCORE) * 100, 1)


def competencies_percent(emp, period):
    """Балл компетенций за период с фолбэком.

    Возвращает (percent, source, used_period):
      source = "period"  — оценки за текущий период;
               "prev"    — оценки за последний период с данными;
               "default" — оценок не было никогда.
    """
    cur = scores_percent(emp, period)
    if cur is not None:
        return cur, "period", period

    hist = (emp or {}).get("scores") or {}
    earlier = sorted((p for p in hist if p != period and p < period), reverse=True)
    for p in earlier:
        v = scores_percent(emp, p)
        if v is not None:
            return v, "prev", p

    return None, "default", None


# ---------------------------------------------------------------- грейд

def grade_for(percent):
    """Грейд по среднему баллу компетенций -> (название, доля премии)."""
    if percent is None:
        return None, 0.0
    name, share = config.GRADES[0][0], config.GRADES[0][2]
    for g in config.GRADES:
        if percent >= g[1]:
            name, share = g[0], g[2]
    return name, share


def grade_with_fallback(emp, period):
    """Грейд с фолбэком на прошлый период.

    Возвращает dict: percent, source, used_period, name, share.
    """
    pct, source, used = competencies_percent(emp, period)

    if source == "default":
        # оценок не было никогда — минимальный грейд с пометкой
        name, share = config.GRADES[0][0], config.GRADES[0][2]
        return {
            "percent": None,
            "source": "default",
            "used_period": None,
            "name": name,
            "share": share,
        }

    name, share = grade_for(pct)
    return {
        "percent": pct,
        "source": source,
        "used_period": used,
        "name": name,
        "share": share,
    }


# ---------------------------------------------------------------- премия

def bonus(salary, grade_share, letter):
    """Премия = оклад × база(20%) × (1 + доля грейда) × коэффициент буквы."""
    if letter is None:
        return 0.0
    k = config.MARK_K.get(letter, 0.0)
    return round(salary * config.BONUS_BASE_RATE * (1 + grade_share) * k, 2)


def bonus_pct(grade_share, letter):
    """Та же премия в процентах оклада — для отчётности."""
    if letter is None:
        return 0.0
    k = config.MARK_K.get(letter, 0.0)
    return round(config.BONUS_BASE_RATE * (1 + grade_share) * k * 100, 1)


# ---------------------------------------------------------------- всё сразу

def evaluate(employee, goals, period=None):
    """Полная раскладка оценки сотрудника за период."""
    period = period or config.PERIOD_DEFAULT
    percent = weighted_percent(goals)
    deploy = overall_deploy(goals)
    letter = letter_for(percent, deploy)

    gr = grade_with_fallback(employee, period)

    # Неполная анкета (решение 29.10.2026): если оценено 90% и меньше
    # приоритетных компетенций, премия не начисляется. Средний балл считается
    # по оценённым, грейд не падает: человек остаётся на грейде без рублей.
    _gc = __import__("grading_compat")
    _row = _gc.scores_for(employee)
    _prio = [c[0] for c in config.COMPS if c[2] == 1]
    _missing = [n for n in _prio if not isinstance(_row.get(n), (int, float))]
    _fill = ((len(_prio) - len(_missing)) * 100.0 / len(_prio)) if _prio else 100.0
    _no_bonus = gr["source"] == "default" or _fill <= 90.0

    return {
        "employee": employee.get("name"),
        "period": period,
        "competency_percent": gr["percent"],
        "grade_source": gr["source"],
        "grade_period": gr["used_period"],
        "grade": gr["name"],
        "grade_share": gr["share"],
        "kpi_percent": percent,
        "deploy": deploy,
        "letter": letter,
        "coef": config.MARK_K.get(letter, 0.0) if letter else None,
        "salary": employee.get("salary"),
        # Премии нет: грейд взят фолбэком (source="default") ИЛИ
        # анкета заполнена на 90% и меньше (решение 29.10.2026).
        "bonus_pct": None if _no_bonus else bonus_pct(gr["share"], letter),
        "bonus": 0 if _no_bonus
                 else bonus(employee.get("salary") or 0, gr["share"], letter),
        "fill_percent": round(_fill, 1),
        "missing_priorities": _missing,
        "goals": [
            {
                "c": g.get("c"),
                "plan": g.get("plan"),
                "fact": g.get("fact"),
                "completion": round(goal_completion(g), 1),
                "status": g.get("status"),
            }
            for g in (goals or [])
        ],
        "empty": percent is None,
    }
