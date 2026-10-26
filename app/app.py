# -*- coding: utf-8 -*-
"""
app.py — веб-интерфейс системы оценки QA (Этап 1)

Запуск:  python app.py   →   http://127.0.0.1:8080

Исправления в этой версии:
  * убран вложенный f-string с тройными кавычками (SyntaxError на Python 3.12);
  * редиректы с кириллицей больше не роняют сервер (UnicodeEncodeError latin-1);
  * параметры URL кодируются через quote();
  * ошибка обработчика показывается в браузере, сервер продолжает работать.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse, quote
import html
import traceback
import urllib.parse

import config
import grading
import state as st

HOST, PORT = "127.0.0.1", 8080

CSS = """
:root{--bg:#0f1216;--card:#171c22;--line:#262d36;--txt:#e6edf3;--muted:#8b98a5;
--acc:#3b82f6;--ok:#22c55e;--warn:#f59e0b;--risk:#ef4444}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
background:var(--bg);color:var(--txt)}
header{padding:16px 24px;border-bottom:1px solid var(--line);display:flex;
gap:8px;align-items:center;flex-wrap:wrap;background:var(--card)}
h1{font-size:16px;margin:0 24px 0 0;white-space:nowrap}
nav a{color:var(--muted);text-decoration:none;padding:6px 12px;border-radius:6px}
nav a:hover{background:#222a33;color:var(--txt)}
nav a.on{background:var(--acc);color:#fff}
main{padding:24px;max-width:1400px}
h2{font-size:18px;margin:0 0 16px}
h3{font-size:14px;margin:24px 0 10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.4px}
tr:hover td{background:#1b2229}
input,select{background:#0f1216;border:1px solid var(--line);color:var(--txt);
border-radius:6px;padding:5px 8px;font:inherit}
button{background:var(--acc);border:0;color:#fff;padding:6px 14px;border-radius:6px;
font:inherit;cursor:pointer}
button.ghost{background:#222a33}
button.ghost.on{background:var(--acc)}
button.del{background:var(--risk)}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px}
.ok{background:rgba(34,197,94,.15);color:var(--ok)}
.warn{background:rgba(245,158,11,.15);color:var(--warn)}
.risk{background:rgba(239,68,68,.15);color:var(--risk)}
.muted{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:24px;margin-top:4px}
.wrap{overflow-x:auto;table-layout:fixed;width:100%}
.prio1{color:#93c5fd}.prio2{color:#a7f3d0}.prio3{color:#fcd34d}
.scores a{text-decoration:none}
pre{background:#0f1216;border:1px solid var(--line);border-radius:8px;padding:12px;
overflow:auto;font-size:12px;color:#fca5a5}
"""

TABS = [("dashboard", "Дашборд"), ("team", "Команда"), ("matrix", "Оценки"),
        ("comps", "Компетенции"), ("goals", "Цели"), ("projects", "Проекты")]


def nav_html(active):
    parts = []
    for key, title in TABS:
        cls = "on" if key == active else ""
        parts.append('<a href="/' + key + '" class="' + cls + '">' + title + "</a>")
    return "".join(parts)


def page(title, body, active=""):
    return (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        "<title>" + html.escape(title) + "</title><style>" + CSS + "</style></head><body>"
        "<header><h1>QA · оценка и грейды</h1><nav>" + nav_html(active) + "</nav></header>"
        "<main>" + body + "</main></body></html>"
    )


def q(s):
    """Кодирование параметра для URL (кириллица)."""
    return quote(str(s), safe="")


def e(s):
    """Экранирование для HTML."""
    return html.escape("" if s is None else str(s))


# ------------------------------------------------------------------ страницы

def page_dashboard(data):
    emps = data["employees"]
    grades = {}
    for emp in emps:
        code, name = grading.grade_of(emp)
        grades[name] = grades.get(name, 0) + 1

    cov = grading.coverage(emps)
    risk = [r for r in cov if r["status"] == "risk"]
    comps_cov = []
    _emp_names = [e.get("name") for e in data.get("employees") or []
                  if isinstance(e, dict) and e.get("name")]
    _cnt = {}
    _who = {}
    for _e in emps:
        _en = _e.get("name") if isinstance(_e, dict) else ""
        _sc = grading.scores_for(e) if isinstance(e, dict) else {}
        for k, v in _sc.items():
            if _v:
                _cnt[_k] = _cnt.get(_k, 0) + 1
                _who.setdefault(_k, []).append(_en)
    for _c in (data.get("competencies") or []):
        _name, _cat, _prio = _c[0], _c[1], _c[2]
        if _prio not in (1, 2):
            continue
        _own = _cnt.get(_name, 0)
        _need = len(emps)
        _st = "risk" if _own <= _need - 2 else ("warn" if _own == _need - 1 else "ok")
        comps_cov.append({"comp": _name, "prio": _prio, "goal": _c[3] if len(_c) > 3 else "",
                          "count": _own, "need": len(emps), "status": _st,
                          "owners": _who.get(_name, [])})

    projects = st.project_coverage(data)
    proj_risk = [p for p in projects if p["status"] == "risk"]

    cards = "".join(
        '<div class="kpi"><span class="muted">' + str(k) + "</span><b>" + str(v) + "</b></div>"
        for k, v in [
            ("Сотрудников", len(emps)),
            ("Компетенций", len(data.get("competencies") or [])),
            ("Проблем в покрытии", len(risk)),
        ]
    )

    order = [g[1] for g in config.GRADES]
    g_rows = "".join(
        "<tr><td>" + e(name) + "</td><td><b>" + str(cnt) + "</b></td></tr>"
        for name, cnt in sorted(grades.items(),
                                key=lambda x: order.index(x[0]) if x[0] in order else 99)
    ) or '<tr><td colspan="2" class="muted">Нет данных</td></tr>'

    r_rows = "".join(
        '<tr><td>' + e(r["comp"]) + '</td>'
        '<td><span class="prio' + str(r["prio"]) + '">п' + str(r["prio"]) + "</span></td>"
        "<td>" + e(r["goal"]) + "</td>"
        "<td>" + str(r["count"]) + " / " + str(r["need"]) + "</td>"
        '<td class="muted">' + e(", ".join(r["owners"]) or "—") + "</td>"
        '<td><span class="badge ' + r["status"] + '">'
        + ("не покрыто" if r["status"] == "risk" else "мало" if r["status"] == "warn" else "ок")
        + "</span></td></tr>"
        for r in comps_cov[:40]
    ) or '<tr><td colspan="6" class="muted">Все компетенции закрыты</td></tr>'

    body = (
        "<h2>Дашборд</h2>"
        '<div class="grid">' + cards + "</div>"
        "<h3>Грейды команды</h3>"
        '<div class="card wrap"><table><tr><th>Грейд</th><th>Человек</th></tr>'
        + g_rows + "</table></div>"
        "<h3>Риски покрытия компетенций (порог 3 балла)</h3>"
        '<div class="card wrap"><table><tr><th>Компетенция</th><th>Приоритет</th>'
        "<th>Цель</th><th>Владеют</th><th>Кто</th><th>Статус</th></tr>" + r_rows + "</table></div>"
    )
    return page("Дашборд", body, "dashboard")


def page_comp_form(data=None, comp=None):
    """Форма добавления/правки компетенции."""
    c = list(comp) if comp else ["", "Проф навыки", 1, ""]
    name = c[0] if len(c) > 0 else ""
    cat = c[1] if len(c) > 1 else ""
    prio = c[2] if len(c) > 2 else 1
    code = c[3] if len(c) > 3 else ""
    opts = "".join(
        '<option value="%s"%s>%s</option>' % (p, " selected" if str(prio) == str(p) else "", p)
        for p in (1, 2, 3))
    body = (
        '<h2>%s</h2>'
        '<div class="card"><form method="get" action="/comps/save">'
        '<input type="hidden" name="name_old" value="%s">'
        '<label>Название: <input name="name" value="%s" required></label><br>'
        '<label>Группа: <input name="cat" value="%s"></label><br>'
        '<label>Код (Ц1, Ц2...): <input name="code" value="%s"></label><br>'
        '<label>Приоритет: <select name="prio">%s</select></label><br>'
        '<button class="btn" type="submit">Сохранить</button> '
        '<a class="btn" href="/comps">Отмена</a>'
        '</form></div>' % (
            "Правка компетенции" if comp else "Новая компетенция",
            e(name), e(name), e(cat), e(code), opts))
    return page("Компетенции", body, "comps")


def page_comps(data=None):
    """Справочник компетенций (чтение)."""
    comps = (data or {}).get("competencies") or list(config.COMPS)
    rows = ""
    for idx, c in enumerate(comps, 1):
        name, cat, prio = c[0], c[1], c[2]
        code = c[3] if len(c) > 3 and c[3] else ""
        cat_full = (cat + (" / " + code if code else "")) if cat else code
        cls = "risk" if prio == 1 else ""
        q = urllib.parse.quote(name)
        rows += ('<tr><td class="muted">%d</td><td>%s</td><td class="muted">%s</td>'
                 '<td><b class="%s">%s</b></td>'
                 '<td><a href="/comps/edit?name=%s">✎</a> '
                 '<a href="/comps/del?name=%s" onclick="return confirm(\'Удалить?\')">✕</a>'
                 '</td></tr>' % (idx, e(name), e(cat_full), cls, prio, q, q))
    body = (
        '<h2>Компетенции</h2>'
        '<p class="muted">Всего: %d. Приоритет 1 — планка 3 балла, '
        'приоритет 2 — 2 балла, приоритет 3 не анализируется.</p>'
        '<p><a class="btn" href="/comps/add">+ Компетенция</a></p>'
        '<table class="tbl"><tr><th>№</th><th>Компетенция</th><th>Группа</th>'
        '<th>Приоритет</th><th></th></tr>%s</table>' % (len(comps), rows))
    return page("Компетенции", body, "comps")


def page_team(data):
    grade_names = dict((g[0], g[1]) for g in config.GRADES)
    rows = ""
    for emp in [x for x in data.get("employees") or [] if isinstance(x, dict)]:
        code, name = grading.grade_of(emp)
        nxt_code, checks = grading.next_grade_gap(emp)
        done = sum(1 for c in checks if c["ok"])
        prog = (str(done) + "/" + str(len(checks))) if checks else "максимум"
        goals = grading.goal_breakdown(emp)
        gtxt = " · ".join(g + ": " + str(v) for g, v in goals.items() if v)
        k = config.GRADE_K.get(code, "—")
        salary = str(int(emp.get("salary", 0))).replace(",", " ")
        rows += (
        "<tr><td><b>" + str(name) + "</b></td>"
            "<td>" + salary + " ₽</td>"
        "<td>" + str(name) + "</td>"
            "<td>" + str(grading.average(emp)) + "</td>"
            "<td>×" + str(k) + "</td>"
            '<td class="muted">' + e(gtxt) + "</td>"
            "<td>→ " + e(grade_names.get(nxt_code, "—"))
            + ' <span class="muted">(' + prog + ")</span></td>"
            '<td><a href="/matrix?emp=' + q(emp.get("name", "-")) + '">'
            '<button class="ghost">оценки</button></a></td></tr>'
        )

    body = (
        '<div class="card"><form method="get" action="/addemp" '
        'style="display:flex;gap:8px;flex-wrap:wrap">'
        '<input name="name" placeholder="ФИО" required style="min-width:220px">'
        '<input name="salary" type="number" min="0" placeholder="Оклад">'
        '<button>Добавить сотрудника</button></form></div>'
        "<h2>Команда</h2>"
        '<p class="muted">Грейд считается по компетенциям (система планок). '
        "Оценка A–E по целям — Этап 2.</p>"
        '<div class="card wrap"><table>'
        "<tr><th>Сотрудник</th><th>Оклад</th><th>Грейд</th><th>Средний балл</th>"
        "<th>K грейда</th><th>Срез по целям</th><th>До следующего грейда</th><th></th></tr>"
        + rows + "</table></div>"
    )
    return page("Команда", body, "team")


def page_matrix(data, emp_name=None):
    if data is None:
        data = st.load()
    comps = (data or {}).get("competencies") or list(config.COMPS)
    emps = [x.get("name") for x in data.get("employees") or [] if isinstance(x, dict) and x.get("name")]
    if not emps:
        return page("Оценки", "<h2>Оценки</h2><div class='card'>Нет сотрудников</div>", "matrix")

    if emp_name not in emps:
        emp_name = emps[0]
    emp = st.find_employee(data, emp_name)

    opts = "".join(
        '<option ' + ("selected" if n == emp_name else "") + ">" + e(n) + "</option>"
        for n in emps
    )

    rows = ""
    for name, cat, prio, goal in comps:
        val = grading.scores_for(emp).get(name, 0)
        cells = ""
        for s in (1, 2, 3, 4, 5):
            url = "/set?emp=" + q(emp_name) + "&comp=" + q(name) + "&v=" + str(s)
            cls = "ghost on" if val == s else "ghost"
            cells += '<a href="' + url + '"><button class="' + cls + '">' + str(s) + "</button></a> "
        clear = ('<a href="/set?emp=' + q(emp_name) + "&comp=" + q(name)
                 + '&v=0"><button class="del">×</button></a>')
        rows += (
            "<tr><td>" + e(name) + "</td>"
            '<td class="muted">' + e(cat) + "</td>"
            '<td><span class="prio' + str(prio) + '">п' + str(prio) + "</span></td>"
            "<td>" + e(goal) + "</td>"
            '<td class="scores">' + cells + " " + clear
            + " <b>" + (str(val) if val else "—") + "</b></td></tr>"
        )

    info = ""
    if emp:
        code, gname = grading.grade_of(emp)
        nxt, checks = grading.next_grade_gap(emp)
        items = "".join(
            "<li>" + ("✅" if c["ok"] else "❌") + " " + e(c["text"]) + "</li>"
            for c in checks
        ) or "<li class='muted'>Грейд максимальный</li>"
        info = (
            '<div class="card"><b>' + e(emp.get("name", "-")) + "</b> — " + e(gname)
            + " · средний балл " + str(grading.average(emp))
            + '<h3 style="margin-bottom:6px">До следующего грейда ('
            + e(dict((g[0], g[1]) for g in config.GRADES).get(nxt, "—")) + ")</h3>"
            '<ul style="margin:0;padding-left:18px">' + items + "</ul></div>"
        )

    body = (
        "<h2>Оценки компетенций</h2>"
        '<form class="card"><label>Сотрудник: '
        '<select name="emp" onchange="this.form.submit()">' + opts + "</select></label></form>"
        + info
        + '<div class="card wrap"><table><tr><th>Компетенция</th><th>Категория</th>'
        "<th>Приоритет</th><th>Цель</th><th>Балл</th></tr>" + rows + "</table></div>"
    )
    return page("Оценки", body, "matrix")


def page_goals(data=None, grade=None):
    """Цели: шаблон по грейду (чтение)."""
    tmpl = (data or {}).get("goals_template", {}) or {}
    grades = [g[0] for g in config.GRADES]
    names = {g[0]: g[1] for g in config.GRADES}
    grade = grade if grade in grades else (grades[0] if grades else None)
    goals = tmpl.get(grade, []) or []

    tabs = "".join(
        '<a href="/goals?grade=%s" style="display:inline-block;margin-right:14px;'
        'padding:6px 10px;border-radius:6px;text-decoration:none;'
        'background:%s;color:%s">%s</a>' % (
            g, "#2563eb" if g == grade else "transparent",
            "#ffffff" if g == grade else "#cccccc",
            e(names.get(g, g)))
        for g in grades)

    cards = ""
    for gz in goals:
        crit = "".join(
            '<div style="padding:4px 0">%s %s</div>' % (
                "●" if c.get("critical") else "○", e(c.get("text", "")))
            for c in gz.get("criteria", []))
        lvl = "выше грейда" if gz.get("level") == "above" else "свой"
        cards += (
            '<div class="card">'
            '<a href="/goals/del?grade=%s&amp;id=%s" style="float:right;margin-left:18px">&#10005;</a>' '<a href="/goals/edit?grade=%s&amp;id=%s" style="float:right">&#9998; править</a>'
            '<b>%s</b> <span class="muted">· %s · уровень: %s</span>'
            '<div class="muted">%s</div>'
            '<div style="margin-top:8px"><b>Критерии:</b></div>%s'
            '</div>' % (
                e(grade), e(gz.get("id", "")),
                e(grade), e(gz.get("id", "")),
                e(gz.get("name", "")),
                "стандартная" if gz.get("type") == "standard" else "доп. задача",
                lvl, e(gz.get("id", "")), crit))

    if not cards:
        cards = '<div class="card muted">У этого грейда целей пока нет.</div>'

    biz = (data or {}).get("goals") or {}
    bparts = []
    for gk in ("Ц1", "Ц2", "Ц3"):
        gd = biz.get(gk) or {}
        mets = "".join(
            '<li style="margin:2px 0">%s</li>' % e(m) for m in (gd.get("metrics") or []))
        bparts.append(
            '<div class="card" style="margin:10px 0">'
            '<div><b>%s</b> &middot; %s '
            '<a href="/goals/biz_edit?goal=%s" style="margin-left:8px">&#9998; править</a></div>'
            '<div class="muted" style="margin-top:6px">Метрики:</div>'
            '<ul style="margin:4px 0 0 18px;padding:0">%s</ul>'
            '</div>' % (e(gk), e(gd.get("name", "")), e(gk), mets))

    body = (
        '<h2>Цели</h2>'
        '<h3 style="margin-top:16px">Бизнес-цели команды</h3>'
        '<p class="muted">Ц1–Ц3 и их метрики. К целям привязаны компетенции '
        'в матрице; правка не меняет закрытые кварталы.</p>'
        + "".join(bparts) +
        '<h3 style="margin-top:24px">Шаблон стандартных целей по грейдам</h3>'
        '<p class="muted">Шаблон стандартных целей по грейдам. '
        'По целям считается оценка A–E за квартал.</p>'
        '<div style="margin:12px 0">' + tabs
        + (' <a href="/goals/new">+ Цель</a>' if grade else '')
        + '</div>'
        + cards)

    return page("Цели", body, "goals")

def page_biz_edit(data, goal, msg=""):
    gk = goal if goal in ("Ц1", "Ц2", "Ц3") else "Ц1"
    gd = (data.get("goals") or {}).get(gk) or {}
    mets = "\n".join(gd.get("metrics") or [])
    body = (
        '<h2>Бизнес-цель %s</h2>' % e(gk)
        + ('<div class="card" style="color:#b00020">%s</div>' % e(msg) if msg else '')
        + '<form method="get" action="/goals/biz_save">'
        '<input type="hidden" name="goal" value="%s">' % e(gk)
        + '<div style="margin:10px 0"><label>Название<br>'
        '<input name="name" value="%s" style="width:420px"></label></div>' % e(gd.get("name", ""))
        + '<div style="margin:10px 0"><label>Метрики — по одной в строке<br>'
        '<textarea name="metrics" rows="10" style="width:520px">%s</textarea></label></div>' % e(mets)
        + '<button type="submit">Сохранить</button> '
        '<a href="/goals" style="margin-left:12px">Отмена</a>'
        '</form>')
    return page("Правка %s" % gk, body, "goals")


def page_goal_new(data, grade, msg=""):
    body = (
        '<h2>Новая цель в грейде %s</h2>' % e(grade)
        + ('<div class="card" style="color:#b00020">%s</div>' % e(msg) if msg else '')
        + '<form method="get" action="/goals/add">'
        + '<input type="hidden" name="grade" value="%s">' % e(grade)
        + '<div style="margin:10px 0"><label>Название<br>'
        + '<input name="name" style="width:520px"></label></div>'
        + '<div style="margin:10px 0"><label>Тип<br><select name="type">'
        + '<option value="standard">стандартная</option>'
        + '<option value="extra">доп. задача</option></select></label></div>'
        + '<div style="margin:10px 0"><label>Уровень<br><select name="level">'
        + '<option value="own">свой</option>'
        + '<option value="above">выше</option></select></label></div>'
        + '<div style="margin:10px 0"><label>Критерии &mdash; по одному в строке, '
        + 'с &#171;!&#187; в начале &mdash; критичный<br>'
        + '<textarea name="criteria" rows="6" style="width:520px"></textarea></label></div>'
        + '<button type="submit">Создать</button> '
        + '<a href="/goals" style="margin-left:12px">Отмена</a></form>')
    return page("Новая цель", body, "goals")


def page_goal_edit(data, grade, gid, msg=""):
    tmpl = (data or {}).get("goals_template") or {}
    lst = tmpl.get(grade) or []
    gz = next((x for x in lst if x.get("id") == gid), None)
    if gz is None:
        return page("Цель не найдена",
                    '<div class="card">Цель %s в грейде %s не найдена. '
                    '<a href="/goals">К списку</a></div>' % (e(gid), e(grade)), "goals")
    crits = "\n".join(
        ("!" if c.get("critical") else "") + c.get("text", "")
        for c in (gz.get("criteria") or []))
    body = (
        '<h2>Правка цели</h2>'
        + ('<div class="card" style="color:#b00020">%s</div>' % e(msg) if msg else '')
        + '<form method="get" action="/goals/save">'
        + '<input type="hidden" name="grade" value="%s">' % e(grade)
        + '<input type="hidden" name="id" value="%s">' % e(gid)
        + '<div style="margin:10px 0"><label>Название<br>'
        + '<input name="name" value="%s" style="width:520px"></label></div>' % e(gz.get("name", ""))
        + '<div style="margin:10px 0"><label>Тип<br><select name="type">'
        + '<option value="standard"%s>стандартная</option>'
        % (' selected' if gz.get("type") == "standard" else '')
        + '<option value="extra"%s>доп. задача</option></select></label></div>'
        % (' selected' if gz.get("type") != "standard" else '')
        + '<div style="margin:10px 0"><label>Уровень<br><select name="level">'
        + '<option value="own"%s>свой</option>'
        % (' selected' if gz.get("level") == "own" else '')
        + '<option value="above"%s>выше</option></select></label></div>'
        % (' selected' if gz.get("level") == "above" else '')
        + '<div style="margin:10px 0"><label>Критерии &mdash; по одному в строке, '
        'с &#171;!&#187; в начале &mdash; критичный<br>'
        + '<textarea name="criteria" rows="6" style="width:520px">%s</textarea></label></div>'
        % e(crits)
        + '<button type="submit">Сохранить</button> '
        + '<a href="/goals?grade=%s" style="margin-left:12px">Отмена</a></form>' % e(grade))
    return page("Правка цели", body, "goals")


def page_projects(data, msg=""):
    emps = [x.get("name") for x in data.get("employees") or [] if isinstance(x, dict) and x.get("name")]
    rows = ""
    for p in st.project_coverage(data):
        owners = ", ".join(n + " (" + str(s) + ")" for n, s in p["owners"].items()) or "—"
        rows += (
            "<tr><td><b>" + e(p["name"]) + "</b></td><td>" + str(len(p["owners"])) + "</td>"
            '<td class="muted">' + e(owners) + "</td><td>" + str(p["count"]) + "</td>"
            '<td><span class="badge ' + p["status"] + '">'
            + ("мало людей" if p["status"] == "risk" else "тесно" if p["status"] == "warn" else "ок")
            + "</span></td>"
            '<td><a href="/delproject?name=' + q(p["name"])
            + '"><button class="del">удалить</button></a></td></tr>'
        )

    eopts = "".join("<option>" + e(n) + "</option>" for n in emps)
    body = (
        "<h2>Проекты</h2>"
        '<p class="muted">Проекты — отдельный слой данных (не компетенции). '
        "Bus factor: мало людей на проекте — риск.</p>"
        + ('<div class="card"><b>' + e(msg) + "</b></div>" if msg else "")
        + '<div class="card"><form method="get" action="/addproject" '
        'style="display:flex;gap:8px;flex-wrap:wrap">'
        '<input name="name" placeholder="Название проекта" required style="min-width:220px">'
        '<select name="owner"><option value="">— владелец —</option>' + eopts + "</select>"
        '<input name="score" type="number" min="1" max="5" value="3" style="width:70px">'
        "<button>Добавить</button></form></div>"
        '<div class="card wrap"><table>'
        "<tr><th>Проект</th><th>Людей</th><th>Владельцы (балл)</th>"
        "<th>Сильных владельцев (≥2)</th><th>Статус</th><th></th></tr>"
        + (rows or '<tr><td colspan="6" class="muted">Проектов нет</td></tr>')
        + "</table></div>"
    )
    return page("Проекты", body, "projects")


def page_error(tb, path):
    body = (
        "<h2>Ошибка обработки запроса</h2>"
        '<div class="card"><p>Путь: <code>' + e(path) + "</code></p>"
        '<p class="muted">Сервер не упал — можно вернуться назад и продолжить.</p></div>'
        '<div class="card"><pre>' + e(tb) + "</pre></div>"
        '<p><a href="/"><button>На дашборд</button></a></p>'
    )
    return page("Ошибка", body)


# ------------------------------------------------------------------ сервер

class H(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(raw)

    def _redirect(self, to):
        # HTTP-заголовки — только latin-1, поэтому кириллицу кодируем
        self.send_response(302)
        self.send_header("Location", quote(to, safe="/?=&%"))
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        qq = parse_qs(u.query, encoding="utf-8")
        p = u.path
        try:
            data = st.load()

            if p in ("/", "/dashboard"):
                return self._send(page_dashboard(data))
            if p == "/team":
                return self._send(page_team(data))
            if p == "/matrix":
                return self._send(page_matrix(data, qq.get("emp", [None])[0]))
            if p == "/comps":
                return self._send(page_comps(data))
            if p == "/goals/save":
                gk = qq.get("grade", [""])[0]
                gid = qq.get("id", [""])[0]
                name = qq.get("name", [""])[0].strip()
                gtype = qq.get("type", ["standard"])[0]
                lvl = qq.get("level", ["own"])[0]
                tmpl = data.setdefault("goals_template", {})
                lst = tmpl.setdefault(gk, [])
                gz = next((x for x in lst if x.get("id") == gid), None)
                if gz is None:
                    return self._send(page_goal_edit(data, gk, gid, "Цель не найдена"))
                if not name:
                    return self._send(page_goal_edit(data, gk, gid, "Название не может быть пустым"))
                if gtype not in ("standard", "extra"):
                    gtype = "standard"
                if lvl not in ("own", "above"):
                    lvl = "own"
                raw = qq.get("criteria", [""])[0]
                old = {c.get("text", ""): c.get("id") for c in (gz.get("criteria") or [])}
                newc, n = [], 0
                for line in raw.split("\n"):
                    t = line.strip()
                    if not t:
                        continue
                    crit = t.startswith("!")
                    if crit:
                        t = t[1:].strip()
                    if not t:
                        continue
                    n += 1
                    cid = old.get(t) or ("c%d" % n)
                    newc.append({"id": cid, "text": t, "critical": crit})
                gz["name"] = name
                gz["type"] = gtype
                gz["level"] = lvl
                gz["criteria"] = newc
                st.save(data)
                return self._redirect("/goals?grade=" + gk)
            if p == "/goals/del":
                gk = qq.get("grade", [""])[0]
                gid = qq.get("id", [""])[0]
                lst = (data.get("goals_template", {}) or {}).get(gk) or []
                if len(lst) <= 1:
                    return self._redirect("/goals?grade=" + gk)
                data["goals_template"][gk] = [x for x in lst if x.get("id") != gid]
                st.save(data)
                return self._redirect("/goals?grade=" + gk)
            if p == "/goals/new":
                gr = qq.get("grade", ["middle1"])[0]
                return self._send(page_goal_new(data, gr))
            if p == "/goals/add":
                gk = qq.get("grade", [""])[0]
                name = qq.get("name", [""])[0].strip()
                if not gk or not name:
                    return self._send(page_goal_new(data, gk, "Название обязательно"))
                tmpl = data.setdefault("goals_template", {})
                lst = tmpl.setdefault(gk, [])
                pre = {"middle1": "mid1", "middle2": "mid2", "middle3": "mid3",
                       "middle4": "mid4", "senior5": "sen5", "senior6": "sen6"}.get(gk, gk[:4])
                n = max([int(x["id"].rsplit("-", 1)[-1])
                         for x in lst if "id" in x and x["id"].rsplit("-", 1)[-1].isdigit()] or [0]) + 1
                gid = "%s-g-%02d" % (pre, n)
                raw = qq.get("criteria", [""])[0]
                crits = []
                for line in raw.split("\n"):
                    t = line.strip()
                    if not t:
                        continue
                    c = t.startswith("!")
                    if c:
                        t = t[1:].strip()
                    if t:
                        crits.append({"id": "c%d" % (len(crits) + 1), "text": t, "critical": c})
                lst.append({
                    "id": gid,
                    "name": name,
                    "type": qq.get("type", ["standard"])[0],
                    "level": qq.get("level", ["own"])[0],
                    "criteria": crits,
                })
                st.save(data)
                return self._redirect("/goals?grade=" + gk)
            if p == "/goals/edit":
                return self._send(page_goal_edit(
                    data, qq.get("grade", [""])[0], qq.get("id", [""])[0]))
            if p == "/goals/biz_edit":
                return self._send(page_biz_edit(data, qq.get("goal", [""])[0]))
            if p == "/goals/biz_save":
                f = qq
                gk = f.get("goal", [""])[0]
                name = f.get("name", [""])[0].strip()
                mets = [x.strip() for x in f.get("metrics", [""])[0].split("\n") if x.strip()]
                d = data
                if gk in ("Ц1", "Ц2", "Ц3") and name:
                    d.setdefault("goals", {})[gk] = {"name": name, "metrics": mets}
                    st.save(d)
                    return self._redirect("/goals")
                return self._send(page_biz_edit(d, gk, "Название не может быть пустым"))
            if p == "/goals":
                return self._send(page_goals(data, qq.get("grade", [None])[0]))
            if p == "/projects":
                return self._send(page_projects(data, qq.get("msg", [""])[0]))

            if p == "/set":
                emp = qq.get("emp", [""])[0]
                comp = qq.get("comp", [""])[0]
                value = qq.get("v", ["0"])[0]
                st.set_score(data, emp, comp, value)
                return self._redirect("/matrix?emp=" + quote(emp, safe=""))

            if p == "/addproject":
                ok = st.add_project(data, qq.get("name", [""])[0],
                                    qq.get("owner", [""])[0] or None,
                                    qq.get("score", ["3"])[0])
                msg = "Проект сохранён" if ok else "Не задано название"
                return self._redirect("/projects?msg=" + quote(msg, safe=""))

            if p == "/delproject":
                st.remove_project(data, qq.get("name", [""])[0])
                return self._redirect("/projects")

            if p == "/emp/del":
                nm = qq.get("name", [""])[0]
                busy = st.remove_employee(data, nm)
                st.save(data)
                msg = "Владелец проектов: " + ", ".join(busy) if busy else "Удалён"
                return self._redirect("/team?msg=" + quote(msg, safe=""))

            if p == "/addemp":
                ok = st.add_employee(data, qq.get("name", [""])[0],
                                     qq.get("salary", ["0"])[0])
                msg = "Добавлен" if ok else "ФИО пустое или уже есть"
                return self._redirect("/team?msg=" + quote(msg, safe=""))

            if p == "/comps":
                return self._send(page_comps(data))
            if p == "/comps/edit":
                nm = qq.get("name", [""])[0]
                comps = data.get("competencies") or []
                cur = next((c for c in comps if c[0] == nm), None)
                if cur is None:
                    return self._redirect("/comps")
                return self._send(page_comp_form(data, cur))
            if p == "/comps/del":
                nm = qq.get("name", [""])[0]
                comps = data.get("competencies") or []
                data["competencies"] = [c for c in comps if c[0] != nm]
                st.save(data)
                return self._redirect("/comps")

            if p == "/comps/save":
                name = (qq.get("name", [""])[0] or "").strip()
                cat = (qq.get("cat", [""])[0] or "").strip()
                code = (qq.get("code", [""])[0] or "").strip()
                ph = qq.get("prio", ["1"])[0]
                prio = int(ph) if ph in ("1", "2", "3") else 1
                old = (qq.get("name_old", [""])[0] or "").strip()
                comps = data.setdefault("competencies", [])
                if not name:
                    return self._send(page_comp_form(data))
                if any(c[0] == name and c[0] != old for c in comps):
                    return self._send(page_comp_form(data))
                cur = next((c for c in comps if c[0] == old), None) if old else None
                if cur is not None:
                    if old != name:
                        for emp in data.get("employees", []):
                            sc = emp.setdefault("scores", {}).setdefault(
                getattr(config, "PERIOD_DEFAULT", "2026-Q4"), {})
                            if old in sc:
                                sc[name] = sc.pop(old)
                    cur[0], cur[1], cur[2], cur[3] = name, cat, prio, code
                else:
                    comps.append([name, cat, prio, code])
                st.save(data)
                return self._redirect("/comps")

            if p == "/comps/add":
                return self._send(page_comp_form(data))

            if p == "/reset":
                st.reset_demo()
                return self._redirect("/")

            return self._send(page("404", "<h2>Страница не найдена</h2>"), 404)

        except Exception:
            return self._send(page_error(traceback.format_exc(), self.path), 500)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("QA Stage 1 -> http://127.0.0.1:8080")
    HTTPServer((HOST, PORT), H).serve_forever()
