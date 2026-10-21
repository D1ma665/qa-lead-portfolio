"""
state.py — данные команды (Этап 1)

Хранятся в state.json:
  employees — сотрудники: имя (условное), оклад, баллы по компетенциям 1–5
  projects  — проекты: название, кто владеет (проект → люди), балл владения

ВАЖНО: все имена демо-данных вымышленные (Иванов, Петров, Сидоров, ...).
Реальные сотрудники в коде и демо-данных не используются.

Компетенции и цели — в config.py (константы).
Проекты заводятся через UI, в config их нет.
"""

import json
import os

import config

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


# ------------------------------------------------------------- демо-данные
# 12 вымышленных сотрудников. Совпадения с реальными людьми случайны.

DEMO_EMPLOYEES = [
    {"name": "Иванов И.И.",      "salary": 150000, "scores": {}},
    {"name": "Петров П.П.",      "salary": 130000, "scores": {}},
    {"name": "Сидоров С.С.",     "salary": 180000, "scores": {}},
    {"name": "Смирнов А.В.",     "salary": 140000, "scores": {}},
    {"name": "Кузнецов Д.А.",    "salary": 120000, "scores": {}},
    {"name": "Волков С.Н.",      "salary": 160000, "scores": {}},
    {"name": "Морозов Д.В.",     "salary": 115000, "scores": {}},
    {"name": "Новиков М.И.",     "salary": 135000, "scores": {}},
    {"name": "Фёдоров А.Р.",     "salary": 120000, "scores": {}},
    {"name": "Соколов С.О.",     "salary": 155000, "scores": {}},
    {"name": "Попова Е.П.",      "salary": 85000,  "scores": {}},
    {"name": "Лебедев Р.Т.",     "salary": 125000, "scores": {}},
]

# Профили для демо: (п1, п2, п3) — типовые баллы по приоритетам
DEMO_PROFILES = [
    (4, 4, 3),  # синьор 6
    (3, 3, 2),  # мидл 4
    (4, 4, 3),  # синьор 6
    (3, 3, 2),  # мидл 4
    (3, 2, 1),  # мидл 3
    (4, 3, 3),  # синьор 5
    (3, 2, 1),  # мидл 3
    (4, 3, 3),  # синьор 5
    (3, 2, 1),  # мидл 3
    (3, 3, 2),  # мидл 4
    (2, 2, 1),  # джун 2
    (3, 2, 1),  # мидл 3
]

DEMO_PROJECTS = [
    {"name": "Проект A", "owners": {"Соколов С.О.": 4, "Попова Е.П.": 3}},
    {"name": "Проект B", "owners": {"Кузнецов Д.А.": 4, "Лебедев Р.Т.": 3}},
    {"name": "Проект C", "owners": {"Кузнецов Д.А.": 3, "Лебедев Р.Т.": 2}},
    {"name": "Проект D", "owners": {"Лебедев Р.Т.": 3, "Соколов С.О.": 2}},
    {"name": "Проект E", "owners": {"Волков С.Н.": 3, "Морозов Д.В.": 3}},
    {"name": "Проект F", "owners": {"Волков С.Н.": 4}},
    {"name": "Проект G", "owners": {"Волков С.Н.": 3, "Лебедев Р.Т.": 3}},
    {"name": "Проект H", "owners": {"Лебедев Р.Т.": 3, "Волков С.Н.": 2}},
    {"name": "Проект I", "owners": {"Морозов Д.В.": 3, "Фёдоров А.Р.": 3}},
    {"name": "Проект J", "owners": {"Морозов Д.В.": 3, "Фёдоров А.Р.": 2}},
    {"name": "Проект K", "owners": {"Новиков М.И.": 3, "Морозов Д.В.": 2}},
    {"name": "Проект L", "owners": {"Новиков М.И.": 4}},
    {"name": "Проект M", "owners": {"Новиков М.И.": 3, "Морозов Д.В.": 1}},
    {"name": "Проект N", "owners": {"Новиков М.И.": 3}},
    {"name": "Проект O", "owners": {"Новиков М.И.": 3}},
]


def _demo_scores(profile):
    """Баллы по всем компетенциям согласно профилю приоритетов."""
    p1, p2, p3 = profile
    out = {}
    for name, _cat, prio, _goal in config.COMPS:
        out[name] = {1: p1, 2: p2, 3: p3}[prio]
    return out


def demo_state():
    emps = []
    for emp, prof in zip(DEMO_EMPLOYEES, DEMO_PROFILES):
        e = dict(emp)
        e["scores"] = _demo_scores(prof)
        emps.append(e)
    return {"employees": emps, "projects": [dict(p) for p in DEMO_PROJECTS]}


# ------------------------------------------------------------- загрузка

def _normalize(data):
    """Приводим данные к актуальному справочнику компетенций."""
    names = [c[0] for c in config.COMPS]
    for emp in data.get("employees", []):
        old = emp.get("scores") or {}
        emp["scores"] = {n: old[n] for n in names if old.get(n) not in (None, "")}
    data.setdefault("projects", [])
    return data


def load():
    if not os.path.exists(PATH):
        data = demo_state()
        save(data)
        return data
    with open(PATH, "r", encoding="utf-8") as f:
        return _normalize(json.load(f))


def save(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reset_demo():
    data = demo_state()
    save(data)
    return data


# ------------------------------------------------------------- выборки

def find_employee(data, name):
    for e in data.get("employees", []):
        if e.get("name") == name:
            return e
    return None


def set_score(data, emp_name, comp, value):
    emp = find_employee(data, emp_name)
    if not emp:
        return False
    if value in (None, "", 0, "0"):
        emp["scores"].pop(comp, None)
    else:
        emp["scores"][comp] = int(value)
    save(data)
    return True


# ------------------------------------------------ проекты (слой данных)

def add_project(data, name, owner=None, score=3):
    name = (name or "").strip()
    if not name:
        return False
    for p in data["projects"]:
        if p["name"].lower() == name.lower():
            if owner:
                p["owners"][owner] = int(score)
                save(data)
            return True
    data["projects"].append({"name": name, "owners": ({owner: int(score)} if owner else {})})
    save(data)
    return True


def remove_project(data, name):
    data["projects"] = [p for p in data["projects"] if p["name"] != name]
    save(data)


def assign_owner(data, project, owner, score=3):
    for p in data["projects"]:
        if p["name"] == project:
            if score in (None, 0, ""):
                p["owners"].pop(owner, None)
            else:
                p["owners"][owner] = int(score)
            save(data)
            return True
    return False


def project_coverage(data, risk_min=2):
    """
    Покрытие проектов: сколько человек владеет, риск если <= risk_min-1.
    Владеет = балл >= 3.
    """
    rows = []
    for p in data.get("projects", []):
        able = {n: s for n, s in p.get("owners", {}).items() if s >= 3}
        n = len(able)
        rows.append({
            "name": p["name"],
            "owners": p.get("owners", {}),
            "able": able,
            "count": n,
            "status": "risk" if n <= risk_min - 1 else ("warn" if n == risk_min else "ok"),
        })
    rows.sort(key=lambda r: (r["status"] != "risk", r["status"] != "warn", r["name"]))
    return rows
