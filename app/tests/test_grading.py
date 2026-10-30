"""Тесты расчёта целей, букв и внедрения. Чистые функции grading.py."""
import pytest

import config
import grading


# ---------------------------------------------------------------- goal_completion

def test_completion_basic():
    g = {"c": "Ц1", "plan": 100, "fact": 105, "status": "done"}
    assert grading.goal_completion(g) == pytest.approx(105.0)


def test_completion_plan_zero_returns_zero():
    # §4.3: плана нет — считаем 0, а не 100
    g = {"c": "Ц1", "plan": 0, "fact": 120, "status": "done"}
    assert grading.goal_completion(g) == 0.0


def test_completion_plan_none_returns_zero():
    g = {"c": "Ц1", "plan": None, "fact": 120, "status": "done"}
    assert grading.goal_completion(g) == 0.0


def test_completion_fact_none_is_zero():
    g = {"c": "Ц1", "plan": 100, "fact": None, "status": "done"}
    assert grading.goal_completion(g) == 0.0


# ---------------------------------------------------------------- active_goals

def test_active_goals_only_done():
    goals = [
        {"c": "Ц1", "status": "done"},
        {"c": "Ц2", "status": "open"},
        {"c": "Ц3", "status": None},
    ]
    assert [g["c"] for g in grading.active_goals(goals)] == ["Ц1"]


def test_active_goals_empty_and_none():
    assert grading.active_goals([]) == []
    assert grading.active_goals(None) == []


# ---------------------------------------------------------------- weights_for

def _g(c, plan=100, fact=100, status="done", deploy="none", tasks=None):
    return {"c": c, "plan": plan, "fact": fact, "status": status,
            "deploy": deploy, "tasks": tasks or []}


def test_weights_three_goals():
    w = grading.weights_for([_g("Ц1"), _g("Ц2"), _g("Ц3")])
    assert w == {"Ц1": 0.4, "Ц2": 0.4, "Ц3": 0.2}
    assert sum(w.values()) == pytest.approx(1.0)


def test_weights_two_goals_sum_one():
    w = grading.weights_for([_g("Ц1"), _g("Ц2")])
    assert sum(w.values()) == pytest.approx(1.0)


def test_weights_one_goal():
    assert grading.weights_for([_g("Ц3")]) == {"Ц3": 1.0}


def test_weights_none_is_empty():
    assert grading.weights_for([]) == {}


# ---------------------------------------------------------------- weighted_percent

def test_weighted_three_goals():
    goals = [_g("Ц1", fact=120), _g("Ц2", fact=90), _g("Ц3", fact=105)]
    # 0.4*120 + 0.4*90 + 0.2*105 = 48 + 36 + 21 = 105.0
    assert grading.weighted_percent(goals) == pytest.approx(105.0)


def test_weighted_example_from_requirements_v24():
    # 0.4*120 + 0.4*90 + 0.2*75 = 48 + 36 + 15 = 99.0
    # в §4.3 v2.4 указано 97.5 — арифметическая ошибка в документе
    goals = [_g("Ц1", fact=120), _g("Ц2", fact=90), _g("Ц3", fact=75)]
    assert grading.weighted_percent(goals) == pytest.approx(99.0)


def test_weighted_yakin_real_data():
    # подтверждено на живых данных: 75 / 70 / 80 -> 74.0
    goals = [_g("Ц1", fact=75), _g("Ц2", fact=70), _g("Ц3", fact=80)]
    assert grading.weighted_percent(goals) == pytest.approx(74.0)


def test_weighted_no_active_goals_is_none():
    goals = [_g("Ц1", status="open"), _g("Ц2", status="open")]
    assert grading.weighted_percent(goals) is None


def test_weighted_unknown_goal_id_weights_renormalized():
    # цель с чужим c выпадает, оставшиеся две получают GOAL_WEIGHTS_TWO
    # (50/50) — сумма весов снова 1.0, итог 100.0
    goals = [_g("Ц1", fact=100), _g("Ц2", fact=100), _g("Ц9", fact=100)]
    assert grading.weighted_percent(goals) == pytest.approx(100.0)


# ---------------------------------------------------------------- letter_for

@pytest.mark.parametrize("percent,deploy,expected", [
    (None, "none", None),
    (0.0, "in_use", "E"),
    (49.9, "in_use", "E"),
    (50.0, "in_use", "D"),
    (69.9, "in_use", "D"),
    (70.0, "in_use", "C"),
    (99.9, "in_use", "C"),
    (100.0, "in_use", "A"),
    (100.0, "deployed", "B"),
    (100.0, "none", "B"),
    (74.0, "deployed", "C"),   # Якин на живых данных
    (105.0, "in_use", "A"),    # Иванов
    (49.6, "none", "E"),       # Фёдоров, §13 п.5.3
    (69.6, "none", "D"),       # Новиков, §13 п.5.3
])
def test_letter_for(percent, deploy, expected):
    assert grading.letter_for(percent, deploy) == expected


# ---------------------------------------------------------------- deploy_from_tasks

def test_deploy_no_tasks_is_none():
    assert grading.deploy_from_tasks({"tasks": []}) == "none"
    assert grading.deploy_from_tasks({}) == "none"


def test_deploy_only_usage_tasks_is_none():
    g = {"tasks": [{"kind": "usage", "done": True}]}
    assert grading.deploy_from_tasks(g) == "none"


def test_deploy_partial_is_none():
    g = {"tasks": [{"kind": "deploy", "done": True},
                   {"kind": "deploy", "done": False}]}
    assert grading.deploy_from_tasks(g) == "none"


def test_deploy_all_deploy_done_without_usage():
    g = {"tasks": [{"kind": "deploy", "done": True},
                   {"kind": "deploy", "done": True}]}
    assert grading.deploy_from_tasks(g) == "deployed"


def test_deploy_all_deploy_and_usage_done_is_in_use():
    g = {"tasks": [{"kind": "deploy", "done": True},
                   {"kind": "usage", "done": True}]}
    assert grading.deploy_from_tasks(g) == "in_use"


def test_deploy_usage_not_done_stays_deployed():
    g = {"tasks": [{"kind": "deploy", "done": True},
                   {"kind": "usage", "done": False}]}
    assert grading.deploy_from_tasks(g) == "deployed"


# ---------------------------------------------------------------- overall_deploy

def test_overall_deploy_best_status_wins():
    goals = [_g("Ц1", deploy="none"),
             _g("Ц2", deploy="deployed"),
             _g("Ц3", deploy="in_use")]
    assert grading.overall_deploy(goals) == "in_use"


def test_overall_deploy_no_goals():
    assert grading.overall_deploy([]) == "none"


def test_overall_deploy_ignores_non_done_goals():
    goals = [_g("Ц1", deploy="in_use", status="open")]
    assert grading.overall_deploy(goals) == "none"


def test_overall_deploy_unknown_status_skipped():
    goals = [_g("Ц1", deploy="legacy-done"), _g("Ц2", deploy="deployed")]
    assert grading.overall_deploy(goals) == "deployed"


def test_overall_deploy_falls_back_to_tasks():
    # deploy не задан — считаем по задачам
    g = {"c": "Ц1", "status": "done", "deploy": None,
         "tasks": [{"kind": "deploy", "done": True},
                   {"kind": "usage", "done": True}]}
    assert grading.overall_deploy([g]) == "in_use"
