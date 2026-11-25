"""Навигация, легенда и путь к state.json.

app.py на импорте поднимает сервер, поэтому его не импортируем:
перечень вкладок достаём из исходника через ast, данные — из state.json.
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
SRC = (APP / "app.py").read_text(encoding="utf-8")


def _tabs():
    tree = ast.parse(SRC)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "TABS" for t in node.targets):
            return [tuple(x) for x in ast.literal_eval(node.value)]
    pytest.fail("TABS не найден в app.py")


def _tab_keys():
    return [k for k, _ in _tabs()]


# ---------------------------------------------------------------- навигация

def test_scores_in_tabs():
    assert "scores" in _tab_keys()


def test_scores_right_after_team():
    keys = _tab_keys()
    assert keys[keys.index("team") + 1] == "scores"


def test_tabs_have_titles():
    for key, title in _tabs():
        assert key and title, (key, title)


# ---------------------------------------------------------------- легенда

def test_team_legend_explains_zero_bonus():
    assert "Почему премия 0" in SRC
    tail = SRC[SRC.index("Почему премия 0"):]
    assert "90%" in tail[:500]


# ---------------------------------------------------------------- state.json

def test_state_path_is_module_relative():
    """Находка 6.1: state.json читается от файла модуля, а не от cwd."""
    code = (
        "import grading_compat as g\n"
        "store = g._all_goals()\n"
        "print(sum(len(v) for v in store.values()))\n"
    )
    env = {**os.environ, "PYTHONPATH": str(APP)}
    out = subprocess.run([sys.executable, "-c", code], cwd="/tmp",
                         capture_output=True, text=True, env=env)
    assert out.returncode == 0, out.stderr
    assert int(out.stdout.strip()) == 13


def test_all_goals_has_current_period():
    import grading_compat as g
    store = g._all_goals()
    assert "2026-Q4" in store
    assert len(store["2026-Q4"]) == 13


def test_goals_for_falls_back_to_store():
    import grading_compat as g
    goals = g._goals_for({"name": "Иванов И.И."})
    assert [x.get("c") for x in goals] == ["Ц1", "Ц2", "Ц3"]


@pytest.mark.data
def test_state_has_expected_employees():
    """6.16: сотрудников не меньше ожидаемого.

    Ловит потерю людей при миграции, но не падает от добавления нового:
    магическое == 13 ломалось при каждом новом сотруднике.
    """
    state = json.loads((APP / "state.json").read_text(encoding="utf-8"))
    people = state.get("employees") or []
    assert len(people) >= 13, (
        "сотрудников стало меньше: %d < 13" % len(people))
    names = [e.get("name") for e in people]
    assert all(names), "у сотрудника нет имени"
    assert len(names) == len(set(names)), "дубли в списке сотрудников"

@pytest.mark.data
def test_employee_goals_use_valid_deploy():
    state = json.loads((APP / "state.json").read_text(encoding="utf-8"))
    allowed = {None, "none", "deployed", "in_use"}
    for period in state.get("employee_goals", {}).values():
        for goals in period.values():
            for g in goals:
                assert g.get("deploy") in allowed, g
