"""Тесты премии и надбавки за грейд (§4.5)."""
import pytest

import config
import grading

BASE = 0.20


# ---------------------------------------------------------- ступени grade_for

@pytest.mark.parametrize("percent,expected_name,expected_share", [
    (0.0,   "Джун 1",   0.0),
    (64.9,  "Джун 1",   0.0),
    (65.0,  "Джун 2",   0.1),
    (74.9,  "Джун 2",   0.1),
    (75.0,  "Мидл 3",   0.15),
    (81.9,  "Мидл 3",   0.15),
    (82.0,  "Мидл 4",   0.2),
    (89.9,  "Мидл 4",   0.2),
    (90.0,  "Сеньор 5", 0.25),
    (95.9,  "Сеньор 5", 0.25),
    (96.0,  "Сеньор 6", 0.3),
    (100.0, "Сеньор 6", 0.3),
])
def test_grade_for_steps(percent, expected_name, expected_share):
    name, share = grading.grade_for(percent)
    assert name == expected_name
    assert share == pytest.approx(expected_share)


def test_grade_share_is_step_not_progress():
    # у всех ниже 65% надбавка одна и та же — 0.0
    assert grading.grade_for(10.0)[1] == grading.grade_for(64.0)[1] == 0.0


# ---------------------------------------------------------- MARK_K / MARK_LABEL

@pytest.mark.parametrize("letter,k", [
    ("A", 1.2), ("B", 1.0), ("C", 0.6), ("D", 0.3), ("E", 0.0),
])
def test_mark_k(letter, k):
    assert config.MARK_K[letter] == pytest.approx(k)


def test_mark_label_c_says_kpi_not_done():
    # §4.4.2: C — «КПИ не выполнены (70–100%)»
    assert "не выполнены" in config.MARK_LABEL["C"]


# ---------------------------------------------------------- таблица премии, %

@pytest.mark.parametrize("letter,share,expected_pct", [
    ("A", 0.0, 24.0), ("A", 0.3, 31.2),
    ("B", 0.0, 20.0), ("B", 0.3, 26.0),
    ("C", 0.0, 12.0), ("C", 0.3, 15.6),
    ("D", 0.0,  6.0), ("D", 0.3,  7.8),
    ("E", 0.0,  0.0), ("E", 0.3,  0.0),
])
def test_bonus_pct_table(letter, share, expected_pct):
    pct = BASE * (1 + share) * config.MARK_K[letter] * 100
    assert pct == pytest.approx(expected_pct, abs=1e-9)


def test_a_on_junior_beats_c_on_senior():
    # §4.5.3: 24% vs 15.6% — KPI решающий
    a_junior = BASE * (1 + 0.0) * config.MARK_K["A"]
    c_senior = BASE * (1 + 0.3) * config.MARK_K["C"]
    assert a_junior > c_senior


# ---------------------------------------------------------- эталонные сотрудники

@pytest.mark.parametrize("salary,share,letter,expected_rub", [
    (150_000, 0.0, "A",  36_000),   # Иванов
    (160_000, 0.1, "A",  42_240),   # Волков
    (135_000, 0.1, "D",   8_910),   # Новиков
])
def test_bonus_rub_reference(salary, share, letter, expected_rub):
    rub = salary * BASE * (1 + share) * config.MARK_K[letter]
    assert round(rub) == expected_rub


def test_bonus_zero_for_e():
    assert 150_000 * BASE * (1 + 0.3) * config.MARK_K["E"] == 0.0


def test_no_grade_constants():
    # §4.4.3: грейд по умолчанию — Джун 1 с надбавкой 0.0
    assert config.GRADES[0][0] == "Джун 1"
    assert config.GRADES[0][2] == 0.0
