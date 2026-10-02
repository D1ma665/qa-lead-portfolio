# app.py — QA Grading System (NiceGUI)
# ---------------------------------------------------------------
# Запуск:  python app.py     (или: python -m app)
# Откроется:  http://localhost:8080
#
# Зависимости: nicegui, pandas, openpyxl
# ---------------------------------------------------------------
from nicegui import ui
import pandas as pd

from config import (APP_NAME, VERSION, COMPS, GRADES, PPL, HISTORY,
                    SCORES, GOALS, BASES, MARK_K)
from grading import build_results
from export_excel import export


# ---------- вспомогательные ----------
def results_df():
    return pd.DataFrame(build_results())


def fmt_rub(x):
    return f"{x:,.0f}".replace(",", " ")


# =========================================================
# СТРАНИЦА «ДАШБОРД»
# =========================================================
@ui.page("/")
def page_dashboard():
    ui.colors(primary="#305496")
    with ui.header().classes("bg-blue-9 items-center"):
        ui.label("🧪 QA Grading System").classes("text-h6 font-bold")
        ui.label(VERSION).classes("text-caption opacity-70 ml-2")

    df = results_df()

    with ui.column().classes("p-4 w-full max-w-6xl mx-auto gap-4"):
        ui.label("ГРЕЙД ← компетенции · ОЦЕНКА ← цели · ПРЕМИЯ = оклад × %грейд × коэф") \
            .classes("text-caption text-grey-7")

        # метрики
        with ui.row().classes("gap-4"):
            with ui.card().classes("w-56"):
                ui.label("Средний % команды").classes("text-caption text-grey-7")
                ui.label(f"{df['% грейд'].mean():.1f}").classes("text-h4 font-bold text-blue-9")
            with ui.card().classes("w-56"):
                ui.label("Фонд премий, ₽").classes("text-caption text-grey-7")
                ui.label(fmt_rub(df['Премия'].sum())).classes("text-h4 font-bold text-green-8")
            with ui.card().classes("w-56"):
                ui.label("Сотрудников").classes("text-caption text-grey-7")
                ui.label(str(len(df))).classes("text-h4 font-bold")

        # таблица
        ui.label("Команда").classes("text-h6 mt-2")
        show_cols = ["Сотрудник", "% грейд", "Грейд", "Оценка", "Премия", "Статус"]
        ui.table.from_pandas(df[show_cols], row_key="Сотрудник").classes("w-full")

        # распределение
        with ui.row().classes("gap-4 w-full"):
            with ui.card().classes("flex-1"):
                ui.label("Распределение по грейдам").classes("text-subtitle1")
                dist = df["Грейд"].value_counts().rename_axis("Грейд").reset_index(name="Кол-во")
                ui.table.from_pandas(dist, row_key="Грейд").classes("w-full")

            with ui.card().classes("flex-1"):
                ui.label("Премии по сотрудникам").classes("text-subtitle1")
                ui.echart({
                    "xAxis": {"type": "category", "data": df["Сотрудник"].tolist()},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "bar", "data": df["Премия"].tolist()}],
                    "grid": {"containLabel": True},
                }).classes("h-64 w-full")

    nav()


# =========================================================
# СТРАНИЦА «КОМАНДА»
# =========================================================
@ui.page("/team")
def page_team():
    with ui.header().classes("bg-blue-9"):
        ui.label("👥 Команда").classes("text-h6 font-bold")

    df = results_df()
    with ui.column().classes("p-4 w-full max-w-6xl mx-auto gap-4"):
        ui.table.from_pandas(df, row_key="Сотрудник").classes("w-full")

        ui.label("История по кварталам").classes("text-h6 mt-4")
        hist_df = pd.DataFrame(
            [{"Сотрудник": p,
              **{f"Q{i+1}": v for i, v in enumerate(HISTORY[p])},
              "Максимум": max(HISTORY[p])} for p in PPL]
        )
        ui.table.from_pandas(hist_df, row_key="Сотрудник").classes("w-full")

    nav()


# =========================================================
# СТРАНИЦА «ОЦЕНКИ»
# =========================================================
@ui.page("/scores")
def page_scores():
    with ui.header().classes("bg-blue-9"):
        ui.label("🎯 Оценки компетенций").classes("text-h6 font-bold")

    with ui.column().classes("p-4 w-full max-w-6xl mx-auto gap-4"):
        ui.label("Балл 1–5 по каждой компетенции. Кнопка сохранит в текущую сессию.") \
            .classes("text-caption text-grey-7")

        person = ui.select(PPL, value=PPL[0], label="Сотрудник").classes("w-64")

        sliders = {}

        @ui.refreshable
        def editors():
            sliders.clear()
            for i, c in enumerate(COMPS):
                name, cat, prio, w, ing = c
                with ui.row().classes("items-center gap-4 w-full"):
                    ui.label(f"{name}  ({cat}, вес {w})").classes("w-96 text-sm")
                    sliders[i] = ui.slider(min=1, max=5, step=1,
                                           value=int(SCORES[person.value][i])).classes("flex-1")

        person.on_value_change(lambda: (editors.refresh()))

        with ui.card().classes("w-full"):
            editors()

        def save():
            SCORES[person.value] = [int(sliders[i].value) for i in range(len(COMPS))]
            ui.notify(f"Баллы для {person.value} обновлены", type="positive")

        ui.button("💾 Применить к сессии", on_click=save).props("color=primary")

        ui.label("Текущая матрица оценок").classes("text-h6 mt-4")
        mdf = pd.DataFrame(
            [[c[0]] + [SCORES[p][i] for p in PPL] for i, c in enumerate(COMPS)],
            columns=["Компетенция"] + PPL,
        )
        ui.table.from_pandas(mdf, row_key="Компетенция").classes("w-full")

    nav()


# =========================================================
# СТРАНИЦА «ЦЕЛИ»
# =========================================================
@ui.page("/goals")
def page_goals():
    with ui.header().classes("bg-blue-9"):
        ui.label("🏁 Цели → Оценка A–E").classes("text-h6 font-bold")

    with ui.column().classes("p-4 w-full max-w-6xl mx-auto gap-4"):
        @ui.refreshable
        def goals_table():
            gdf = pd.DataFrame(GOALS).rename(columns={
                "person": "Сотрудник", "goal": "Цель", "c": "Ц.",
                "pct": "% вып.", "over": "Перевыполнил"})
            ui.table.from_pandas(gdf).classes("w-full")
        goals_table()

        ui.label("Добавить цель").classes("text-h6 mt-4")
        with ui.card().classes("w-full"):
            with ui.row().classes("gap-4"):
                p = ui.select(PPL, value=PPL[0], label="Сотрудник").classes("w-56")
                goal = ui.input("Цель").classes("flex-1")
                cc = ui.select(["Ц1", "Ц2", "Ц3"], value="Ц1", label="Привязка").classes("w-32")
            with ui.row().classes("gap-4 items-center"):
                pct = ui.slider(min=0, max=150, value=100).classes("flex-1")
                over = ui.checkbox("Перевыполнил (инструмент автоматизации)")

            def add():
                if not goal.value:
                    ui.notify("Введи название цели", type="warning")
                    return
                GOALS.append({"person": p.value, "goal": goal.value, "c": cc.value,
                              "pct": int(pct.value), "over": over.value})
                ui.notify(f"Цель «{goal.value}» добавлена", type="positive")
                goal.value = ""
                goals_table.refresh()

            ui.button("➕ Добавить", on_click=add).props("color=primary")

        ui.label("Расчётная оценка").classes("text-h6 mt-4")
        df = results_df()[["Сотрудник", "% цели", "Оценка", "Смысл"]]
        ui.table.from_pandas(df, row_key="Сотрудник").classes("w-full")

    nav()


# =========================================================
# СТРАНИЦА «ПРЕМИЯ»
# =========================================================
@ui.page("/salary")
def page_salary():
    with ui.header().classes("bg-blue-9"):
        ui.label("💰 Калькулятор премии").classes("text-h6 font-bold")

    df = results_df()

    with ui.column().classes("p-4 w-full max-w-3xl mx-auto gap-4"):
        ui.label("Меняй оклад или грейд — премия пересчитается на лету.") \
            .classes("text-caption text-grey-7")

        with ui.card().classes("w-full"):
            person = ui.select(PPL, value=PPL[0], label="Сотрудник").classes("w-64")
            row = df[df["Сотрудник"] == PPL[0]].iloc[0]

            base = ui.number("Оклад, ₽", value=int(BASES.get(PPL[0], 0)),
                             step=5000, format="%0.0f").classes("w-64")
            pc = ui.select([g[2] for g in GRADES],
                           value=GRADES[max(row["gidx"], 0)][2],
                           label="% премии по грейду").classes("w-64")
            coef = ui.select(list(MARK_K.values()), value=row["Коэф."],
                             label="Коэф. оценки").classes("w-64")

            result = ui.label().classes("text-h4 font-bold text-green-8 mt-4")

            def recalc():
                prem = round((base.value or 0) * pc.value * coef.value)
                result.text = f"Премия: {fmt_rub(prem)} ₽"
            base.on_value_change(lambda: recalc())
            pc.on_value_change(lambda: recalc())
            coef.on_value_change(lambda: recalc())
            recalc()

            ui.code("ПРЕМИЯ = оклад × %премии(грейд) × коэффициент(оценка)")

    nav()


# =========================================================
# СТРАНИЦА «ЭКСПОРТ»
# =========================================================
@ui.page("/export")
def page_export():
    with ui.header().classes("bg-blue-9"):
        ui.label("📥 Экспорт в Excel").classes("text-h6 font-bold")

    with ui.column().classes("p-4 w-full max-w-3xl mx-auto gap-4"):
        ui.label("Выгружает текущее состояние (Дашборд, Компетенции, Оценки, Грейды).") \
            .classes("text-caption text-grey-7")

        status = ui.label()

        def do_export():
            path = export("QA_System.xlsx")
            status.text = f"✅ Файл готов: {path}"
            ui.notify("Excel сформирован", type="positive")

        ui.button("📥 Сформировать QA_System.xlsx", on_click=do_export).props("color=primary")
        ui.label("Файл появится в папке проекта рядом с app.py").classes("text-caption text-grey-7")

    nav()


# =========================================================
# ПЛАВАЮЩАЯ НАВИГАЦИЯ
# =========================================================
def nav():
    with ui.row().classes("fixed bottom-0 left-0 w-full bg-white shadow-2 justify-center gap-2 p-2"):
        ui.button("📊 Дашборд", on_click=lambda: ui.navigate.to("/")).props("flat")
        ui.button("👥 Команда", on_click=lambda: ui.navigate.to("/team")).props("flat")
        ui.button("🎯 Оценки", on_click=lambda: ui.navigate.to("/scores")).props("flat")
        ui.button("🏁 Цели", on_click=lambda: ui.navigate.to("/goals")).props("flat")
        ui.button("💰 Премия", on_click=lambda: ui.navigate.to("/salary")).props("flat")
        ui.button("📥 Экспорт", on_click=lambda: ui.navigate.to("/export")).props("flat")


ui.run(title=APP_NAME, dark=False, reload=False, host="0.0.0.0", port=8080)
