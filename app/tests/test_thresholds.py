"""Пороги 29.10.2026: min_avg в LADDER, порог п1, блок премии при анкете <= 90%.

Держат решения из журнала §14 и реестр §13:
  п. 6.28 — min_avg по ступеням 3.25 / 3.75 / 4.10 / 4.50 / 4.80
  п. 6.29/6.32 — порог приоритетной компетенции 3, не 4
  п. 6.30 — премия обнуляется при заполнении приоритетных 90% и ниже
"""
import config
import grading
import grading_compat as compat


# -------------------------------------------------------- вспомогательное

P1 = [c[0] for c in config.COMPS if c[2] == 1]   # приоритетные, их 20


def _emp(scores=None, name="Тест Т.Т.", salary=100_000):
    """scores_for читает emp["scores"][period], а не periods[...]["scores"]."""
    period = config.PERIOD_DEFAULT
    return {"name": name, "salary": salary,
            "scores": {period: scores or {}},
            "periods": {period: {"scores": scores or {}}}}


def _goal(c, fact=100, deploy="in_use"):
    return {"c": c, "plan": 100, "fact": fact, "status": "done",
            "deploy": deploy, "tasks": []}


def _goals():
    return [_goal("Ц1", 100), _goal("Ц2", 100), _goal("Ц3", 100)]


def _profile(score, n=20):
    """n приоритетных компетенций с одинаковым баллом."""
    return dict((name, score) for name in P1[:n])


# -------------------------------------------------------- min_avg в LADDER

def test_ladder_min_avg_values():
    """Пороги ступеней зафиксированы: правка требует решения (п. 6.28)."""
    got = dict((code, mn) for code, _name, mn in compat.LADDER)
    assert got["J1"] == 3.25
    assert got["J2"] == 3.75
    assert got["M3"] == 4.10
    assert got["M4"] == 4.50
    assert got["S5"] == 4.80


def test_p1_threshold_is_3():
    """Балл 3 проходит порог, 2 — нет (п. 6.29/6.32)."""
    emp = _emp(_profile(3))
    _, checks = compat.next_grade_gap(emp)
    p1 = [c for c in checks if c["text"].startswith("п1")]
    assert p1 and p1[0]["ok"] is True, "балл 3 должен проходить"

    emp_low = _emp(_profile(2))
    _, checks_low = compat.next_grade_gap(emp_low)
    p1_low = [c for c in checks_low if c["text"].startswith("п1")]
    assert p1_low and p1_low[0]["ok"] is False, "балл 2 не проходит"
    assert ">= 3" in p1_low[0]["text"], "подпись порога без устаревшей четвёрки"


def test_p1_counts_only_scored():
    """Знаменатель — оценённые, не все 20 (п. 6.9)."""
    scores = dict((name, 3) for name in P1[:10])
    _, checks = compat.next_grade_gap(_emp(scores))
    p1 = [c for c in checks if c["text"].startswith("п1")][0]
    assert "10/10" in p1["text"]


# -------------------------------------------------------- блок премии

def test_bonus_blocked_at_90_percent():
    """18 из 20 приоритетных = 90% — премия не начисляется (п. 6.30)."""
    emp = _emp(_profile(4, n=18))
    r = grading.evaluate(emp, _goals())
    assert r["fill_percent"] == 90.0
    assert r["bonus"] == 0
    assert len(r["missing_priorities"]) == 2


def test_bonus_kept_at_95_percent():
    """19 из 20 = 95% — премия остаётся (п. 6.30)."""
    emp = _emp(_profile(4, n=19))
    r = grading.evaluate(emp, _goals())
    assert r["fill_percent"] == 95.0
    assert r["bonus"] > 0


def test_bonus_zero_without_grades():
    """Пустой профиль: grade_source = default, премия 0 (п. 1.2/4.4.3)."""
    r = grading.evaluate(_emp(), _goals())
    assert r["bonus"] == 0
    assert r["bonus_pct"] is None


def test_next_grade_gap_shows_next_step_threshold():
    """Средняя 3.60 = J2; следующая ступень M3, порог 4.10 балла (п. 6.28)."""
    emp = _emp(_profile(3.6))
    code, checks = compat.next_grade_gap(emp)
    assert code == "M3"
    avg = [c for c in checks if "средняя" in c["text"]][0]
    assert "3.60" in avg["text"]
    assert "4.10" in avg["text"], "порог следующей ступени, не текущей"
    assert avg["ok"] is False
