"""migrate.py — миграция state.json к модели целей по периодам.

Создаёт слой state["employee_goals"]:

    "employee_goals": {
        "2026-Q4": {
            "Иванов И.М.": [
                {"c": "Ц1", "plan": 100, "fact": 0, "period": "2026-Q4",
                 "status": "open",
                 "tasks": [{"id": "t1", "text": "...", "kind": "deploy",
                            "critical": true, "done": false}],
                 "deploy": "none",
                 "owner": "руководитель",}

            ]
        }
    }

Запуск:
    python3 migrate.py --dry     # только показать, ничего не писать
    python3 migrate.py           # применить (с бэкапом)
"""

import json
import shutil
import sys
import os
from datetime import datetime

import config

STATE = "state.json"
BACKUP_DIR = "backups"


def now_tag():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"state_before_migrate_{now_tag()}.json")
    shutil.copy(STATE, dst)
    return dst


def empty_goal(goal_id, period):
    """Новая цель сотрудника в состоянии 'не поставлена'."""
    return {
        "c": goal_id,
        "period": period,
        "plan": 100,          # план — % выполнения (100 = выполнить ровно)
        "fact": 0,            # факт до закрытия периода
        "status": "open",     # open | done | moved | dropped
        "tasks": [],          # задачи-критерии: kind = deploy | usage
        "deploy": "none",     # none | deployed | in_use
        "extra": None,        # доп. задание: {"text":..., "metric":..., "by":...}
        "closed_by": None,    # кто закрыл период
    }


def migrate(state, period=None):
    """Идемпотентно добавляет employee_goals. Возвращает (state, отчёт)."""
    period = period or config.PERIOD_DEFAULT
    report = []

    eg = state.setdefault("employee_goals", {})

    # --- справочник целей: убеждаемся, что Ц1–Ц3 на месте
    goals = state.get("goals") or {}
    for gid in config.GOAL_IDS:
        if gid not in goals:
            meta = next((b for b in config.BIZ_GOALS
                         if b["id"] == "U" + gid[1]), {})
            goals[gid] = {"name": meta.get("name", gid), "metrics": []}
            report.append(f"добавлен справочник {gid}")
    state["goals"] = goals

    # --- период
    bucket = eg.setdefault(period, {})
    report.append(f"период {period}: {len(bucket)} сотрудников")

    # --- сотрудники: создаём пустые наборы целей, если их нет
    for emp in state.get("employees", []):
        name = emp.get("name")
        if not name:
            continue
        if name in bucket:
            continue
        bucket[name] = [empty_goal(gid, period) for gid in config.GOAL_IDS]
        report.append(f"  + {name}: Ц1, Ц2, Ц3 (план 100, факт 0)")

    # --- миграция оценок: {"2026-Q4": {...}} уже правильная,
    #     но если встретился плоский dict {comp: score} — оборачиваем
    for emp in state.get("employees", []):
        sc = emp.get("scores")
        if isinstance(sc, dict) and sc:
            keys = list(sc)
            if not any(k.startswith("20") for k in keys):
                emp["scores"] = {period: sc}
                report.append(f"  ! {emp.get('name')}: scores обёрнут в {period}")

    return state, report


def main():
    dry = "--dry" in sys.argv

    with open(STATE, encoding="utf-8") as f:
        state = json.load(f)

    state, report = migrate(state)

    print("--- ОТЧЁТ ---")
    for line in report:
        print(line)

    if dry:
        print("\n[dry] ничего не записано")
        return

    path = backup()
    print(f"\nбэкап: {path}")

    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

    print("state.json обновлён")


if __name__ == "__main__":
    main()
