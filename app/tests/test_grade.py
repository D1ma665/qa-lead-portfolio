"""Тесты грейдов, совместимости и evaluate.

Держат регрессии из журнала §13:
  2.1/19 — grade_raise удалён
  регрессия 29.10.2026 — grade_of НЕ подставляет название в поле кода
  п. 6.1 — _all_goals не должен зависеть от текущего каталога
"""
import os

import pytest

import config
import grading
import grading_compat as compat


# -------------------------------------------------------- вспомогательное

def _emp(scores=None, name="Тест Т.Т.", salary=100_000):
    # Схема как в state.json: emp["scores"][период] = {компетенция: балл}.
    # scores_for (grading_compat) читает именно этот путь, не periods.
    return {"name": name, "salary": salary,
            "scores": {"2026-Q4": scores or {}}}


P1 = [c[0] for c in config.COMPS if c[2] == 1]


def _profile(score=3.6, n=20):
    """Оценённая анкета: n приоритетных компетенций с баллом score.

    Нужна, чтобы grade_source стал "scores": при пустой анкете source =
    "default" и буква по §4.4.3/6.14 не считается.
    """
    return dict((name, score) for name in P1[:n])


def _goal(c, fact=100, deploy="deployed"):
    return {"c": c, "plan": 100, "fact": fact, "status": "done",
            "deploy": deploy, "tasks": []}


# -------------------------------------------------------- где что живёт

def test_average_only_in_compat():
    assert hasattr(compat, "average")
    assert not hasattr(grading, "average")


def test_grade_of_only_in_compat():
    assert hasattr(compat, "grade_of")
    assert not hasattr(grading, "grade_of")


def test_grade_raise_removed():
    """§13 п.2.1/19: grade_raise — мёртвый код, удалён."""
    assert not hasattr(compat, "grade_raise")
    assert not hasattr(grading, "grade_raise")


# -------------------------------------------------------- компетенции

def test_scores_percent_empty_is_none():
    """Нет оценок -> None (нет данных), а не 0.0."""
    assert grading.scores_percent(_emp(), "2026-Q4") is None


def test_average_empty_is_zero():
    assert compat.average(_emp()) == 0.0


# -------------------------------------------------------- РЕГРЕССИЯ grade_of

def test_grade_of_returns_ladder_code():
    """Код грейда берётся из LADDER: "Джун 1" -> "J1".

    Раньше grade_of возвращал ("", "нет грейда") для пустого профиля,
    из-за чего next_grade_gap отдавал "J1" всем (п. 6.5-6.7).
    """
    code, name = compat.grade_of(_emp())
    assert code == "J1"
    assert name == "Джун 1"



def test_grade_of_code_is_not_name():
    code, name = compat.grade_of(_emp())
    assert code != name


# -------------------------------------------------------- РЕГРЕССИЯ next_grade_gap

def test_next_grade_gap_shape():
    """Возвращает (код следующего грейда, список критериев).

    Пустой профиль: грейд J1, следующий -> J2.
    """
    code, checks = compat.next_grade_gap(_emp())
    assert code == "J2"
    assert isinstance(checks, list)



def test_next_grade_gap_reports_missing_profile():
    _, checks = compat.next_grade_gap(_emp())
    assert checks, "критерии должны быть непустыми"


def test_next_grade_gap_code_is_string():
    code, _ = compat.next_grade_gap(_emp())
    assert isinstance(code, str)


# -------------------------------------------------------- grade_with_fallback

def test_grade_with_fallback_default_source():
    g = grading.grade_with_fallback(_emp(), "2026-Q4")
    assert g["name"] == config.GRADES[0][0]
    assert g.get("source") == "default"


# -------------------------------------------------------- bonus / bonus_pct

@pytest.mark.parametrize("letter,share,expected_rub", [
    ("A", 0.0,  24_000),
    ("A", 0.3,  31_200),
    ("B", 0.0,  20_000),
    ("C", 0.3,  15_600),
    ("D", 0.0,   6_000),
    ("E", 0.3,       0),
])
def test_bonus_function(letter, share, expected_rub):
    assert round(grading.bonus(100_000, share, letter)) == expected_rub


def test_bonus_pct_consistent_with_bonus():
    pct = grading.bonus_pct(0.1, "A")
    rub = grading.bonus(100_000, 0.1, "A")
    assert rub == pytest.approx(100_000 * pct / 100)


# -------------------------------------------------------- evaluate

def test_evaluate_yakin():
    """Живые данные: 75/70/80 при планах 100 -> 74.0, буква C."""
    r = grading.evaluate(_emp(_profile(), name="Якин А.В."),
                         [_goal("Ц1", 75), _goal("Ц2", 70), _goal("Ц3", 80)],
                         "2026-Q4")
    assert r["kpi_percent"] == pytest.approx(74.0)
    assert r["letter"] == "C"


def test_evaluate_default_grade_no_bonus():
    """§4.4.3 + §4.5.4: default -> bonus_pct None, bonus 0, share 0.0."""
    r = grading.evaluate(_emp(name="Якин А.В."),
                         [_goal("Ц1"), _goal("Ц2"), _goal("Ц3")],
                         "2026-Q4")
    assert r["bonus_pct"] is None
    assert r["bonus"] == 0
    assert r["grade_share"] == 0.0


def test_evaluate_no_goals():
    r = grading.evaluate(_emp(), [], "2026-Q4")
    assert r["kpi_percent"] is None
    assert r["letter"] is None


def test_evaluate_a_vs_b():
    """A требует in_use, иначе B при тех же 100%+."""
    goals = [_goal("Ц1", 120), _goal("Ц2", 120), _goal("Ц3", 120)]
    assert grading.evaluate(_emp(_profile()), goals, "2026-Q4")["letter"] == "B"
    for g in goals:
        g["deploy"] = "in_use"
    assert grading.evaluate(_emp(_profile()), goals, "2026-Q4")["letter"] == "A"


# -------------------------------------------------------- п. 6.1 — путь целей

def test_all_goals_returns_dict():
    goals = compat._all_goals()
    assert isinstance(goals, dict)
    assert goals, "_all_goals вернул {} — проверить state.json"


def test_all_goals_independent_of_cwd():
    """п. 6.1: open("state.json") — относительный путь, вне app/ тихо даёт {}."""
    cwd = os.getcwd()
    try:
        os.chdir("/")
        goals = compat._all_goals()
    finally:
        os.chdir(cwd)
    assert goals, ("_all_goals вернул {} вне каталога app/: "
                   "относительный путь state.json")
