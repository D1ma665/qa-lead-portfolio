from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from config import COMPS, GRADES, PPL
from grading import build_results, comp_pct

H_FONT = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="305496")
SIDE = Side(style="thin", color="BFBFBF")
BD = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _head(ws, r, headers):
    for i, t in enumerate(headers, 1):
        c = ws.cell(r, i, t)
        c.font, c.fill, c.alignment, c.border = H_FONT, FILL, CENTER, BD


def _row(ws, r, values):
    for i, v in enumerate(values, 1):
        c = ws.cell(r, i, v)
        c.border, c.alignment = BD, CENTER


def _widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w


def export(path="QA_System.xlsx", results=None, scores=None, goals=None):
    if results is None:
        results = build_results()
    if scores is None:
        from config import SCORES as scores
    if goals is None:
        from config import GOALS as goals

    people = [r["Сотрудник"] for r in results]
    wb = Workbook()

    ws = wb.active
    ws.title = "Дашборд"
    headers = ["Сотрудник", "% компетенций", "Грейд", "% премии", "Оценка",
               "% цели", "Премия", "Коэф.", "Статус", "Оклад"]
    _head(ws, 1, headers)
    for i, rc in enumerate(results):
        _row(ws, i + 2, [rc[h] for h in headers])
        ws.cell(i + 2, 2).number_format = "0.00"
        ws.cell(i + 2, 4).number_format = "0%"
        ws.cell(i + 2, 7).number_format = "# ##0"
        ws.cell(i + 2, 10).number_format = "# ##0"
    n = len(results) + 3
    ws.cell(n, 1, "Фонд премий, руб.:").font = Font(bold=True)
    c = ws.cell(n, 7, sum(r["Премия"] for r in results))
    c.font, c.number_format = Font(bold=True), "# ##0"
    _widths(ws, [20, 15, 12, 10, 10, 10, 14, 8, 14, 12])
    ws.freeze_panes = "A2"

    ws2 = wb.create_sheet("Компетенции")
    _head(ws2, 1, ["Компетенция", "Категория", "Приоритет", "Вес", "В грейд?"])
    for i, comp in enumerate(COMPS):
        _row(ws2, i + 2, list(comp))
    _widths(ws2, [40, 16, 11, 8, 11])
    ws2.freeze_panes = "A2"

    ws3 = wb.create_sheet("Оценки")
    _head(ws3, 1, ["Компетенция"] + people + ["В грейд?"])
    for idx, comp in enumerate(COMPS):
        vals = [scores.get(p, [])[idx] if idx < len(scores.get(p, [])) else "" for p in people]
        _row(ws3, idx + 2, [comp[0]] + vals + [comp[4]])
    r_end = len(COMPS) + 3
    ws3.cell(r_end, 1, "% компетенций").font = Font(bold=True)
    for j, p in enumerate(people, 2):
        cell = ws3.cell(r_end, j, comp_pct(scores.get(p, [1] * len(COMPS))))
        cell.font, cell.number_format = Font(bold=True), "0.00"
    _widths(ws3, [40] + [14] * len(people) + [10])
    ws3.freeze_panes = "B2"

    ws5 = wb.create_sheet("Цели")
    _head(ws5, 1, ["Сотрудник", "Цель", "Привязка", "% вып.", "Перевыполнил"])
    for i, g in enumerate(goals):
        _row(ws5, i + 2, [g["person"], g["goal"], g.get("c", ""), g["pct"],
                          "Да" if g["over"] else "Нет"])
    _widths(ws5, [20, 40, 10, 10, 14])
    ws5.freeze_panes = "A2"

    ws4 = wb.create_sheet("Грейды")
    _head(ws4, 1, ["Грейд", "Порог %", "% премии"])
    for i, g in enumerate(GRADES):
        _row(ws4, i + 2, [g[0], g[1], g[2]])
        ws4.cell(i + 2, 3).number_format = "0%"
    _widths(ws4, [16, 10, 10])

    wb.save(path)
    return path
