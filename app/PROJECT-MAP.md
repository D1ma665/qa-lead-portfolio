# Карта проекта

## Файлы
      24 _archive/patch3.py
      30 _archive/patch4.py
      33 _archive/patch2.py
      34 _archive/patch_g.py
      85 _archive/add_sql.py
      96 export_excel.py
     125 close_goals.py
     131 page_scores.py
     132 migrate.py
     138 _archive/fix_junior.py
     141 comps.py
     167 config.py
     189 close_goal.py
     189 grades_check.py
     194 grading_compat.py
     238 grading.py
     277 state.py
     772 app.py
    2995 total

## Какие модули что экспортируют
### app.py
14:from http.server import BaseHTTPRequestHandler, HTTPServer
15:from urllib.parse import parse_qs, urlparse, quote
16:import html
17:import traceback
18:import urllib.parse
20:import config
21:from page_scores import page_scores as scores_body
22:import grading as grading_core
23:import grading_compat as grading
24:import state as st
74:def nav_html(active):
82:def page(title, body, active=""):
91:def q(s):
96:def e(s):
103:def page_dashboard(data):
179:def page_comp_form(data=None, comp=None):
205:def page_comps(data=None):
230:def page_team(data):
281:def page_matrix(data, emp_name=None):
344:def page_goals(data=None, grade=None):
414:def page_biz_edit(data, goal, msg=""):
433:def page_goal_new(data, grade, msg=""):
455:def page_goal_edit(data, grade, gid, msg=""):
493:def page_projects(data, msg=""):
529:def page_error(tb, path):
542:class H(BaseHTTPRequestHandler):

### close_goal.py
15:import json
16:import shutil
17:import sys
18:import os
19:from datetime import datetime
21:import config
27:def backup():
36:def load():
41:def save(state):
46:def find_goal(state, name, gid, period=None):
59:def cmd_list(state, period=None):
81:def cmd_set(state, name, gid, pairs):
104:def cmd_status(state, name, gid, value):
108:def cmd_task(state, name, gid, action, rest):
143:def _recalc_deploy(tasks):
153:def main():

### close_goals.py
17:import json
18:import shutil
19:import sys
20:from datetime import datetime
51:def kpi(goals):
55:def letter(goals):
70:def main(apply):

### comps.py
12:import config
15:def grade_level(grade):
22:def comp_level(comp):
27:def comp_name(comp):
31:def available_comps(grade):
37:def split_scores(scores, grade):
67:def percent_of(pairs):
75:def competency_percent(scores, grade):
83:def reserved_percent(scores, grade):
89:def next_grade(grade):
98:def readiness(scores, grade):
128:def report(scores, grade):

### config.py
127:def lift(letter, steps=1):

### export_excel.py
1:from openpyxl import Workbook
2:from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
4:from config import COMPS, GRADES, PPL
5:from grading import build_results, comp_pct
14:def _head(ws, r, headers):
20:def _row(ws, r, values):
26:def _widths(ws, widths):
31:def export(path="QA_System.xlsx", results=None, scores=None, goals=None):

### grades_check.py
24:import json
25:import sys
27:import config
45:def by_priority(row, prio):
51:def average(row):
56:def need_min(row, prio, threshold):
64:def incomplete(row, priorities):
70:def check(row, grade):
129:def max_grade(row):
148:def analyse(emp):
164:def main():

### grading.py
19:import config
24:def active_goals(goals):
29:def goal_completion(goal):
38:def weights_for(goals):
50:def weighted_percent(goals):
67:def letter_for(percent, deploy="none"):
80:def deploy_from_tasks(goal):
94:def overall_deploy(goals):
109:def scores_percent(emp, period):
118:def competencies_percent(emp, period):
142:def grade_for(percent):
153:def grade_with_fallback(emp, period):
183:def bonus(salary, grade_share, letter):
191:def bonus_pct(grade_share, letter):
201:def evaluate(employee, goals, period=None):

### grading_compat.py
17:import json
19:import config
20:import grading
30:def _period(emp):
37:def scores_for(emp):
45:def _scored(emp):
50:def average(emp):
58:def average_percent(emp):
67:def grade_of(emp):
89:def _grade_index(name):
96:def grade_raise(emp):
104:def coverage(emps):
130:def _check(ok, text):
134:def next_grade_gap(emp):
164:def _goals_store():
173:def _goals_for(emp):
180:def goal_breakdown(emp):

### migrate.py
24:import json
25:import shutil
26:import sys
27:import os
28:from datetime import datetime
30:import config
36:def now_tag():
40:def backup():
47:def empty_goal(goal_id, period):
62:def migrate(state, period=None):
106:def main():

### page_scores.py
2:from html import escape as e
5:def _emps(data):
9:def _period(data):
19:def _goals_of(emp):
29:def _pct(plan, fact):
37:def _weighted(goals):
59:def _deploy(goals):
67:def _letter(pct, deploy="none"):
77:def _cls(letter):
87:def _money(v):
94:def _cell(v):
98:def page_scores(data):

### state.py
1:import config
16:import json
17:import os
18:import copy
20:import config
78:def _demo_scores(profile, data=None):
93:def demo_state():
108:def _normalize(data):
130:def load():
139:def save(data):
144:def reset_demo():
152:def find_employee(data, name):
159:def set_score(data, emp, comp, value, period=None):
194:def add_project(data, name, owner=None, score=3):
209:def remove_project(data, name):
214:def remove_employee(data, name):
225:def assign_owner(data, project, owner, score=3):
237:def project_coverage(data, risk_min=None):
259:def add_employee(data, name, salary=0, scores=None):


## Ловушки

1. ~~`import grading_compat as grading`~~ — исправлено 28.10.2026:
   `import grading` + `import grading_compat as compat`. Перекрытия нет.
2. ~~`grading_compat.grade_raise()`~~ — удалена 28.10.2026 (мёртвый код).
3. ~~`goal_breakdown()`: `plan or 100`~~ — исправлено 28.10.2026: `plan or 0` + ветка
   «нет плана», как в `grading.py:31`.
4. **Веса целей — только 40/40/20** (`config.GOAL_WEIGHTS`), requirements-v2.4 §4.3.
   Паритет 1/3 отменён 28.10; попытка вернуть его откачена в тот же день.
   Менять только вместе с правкой §4.3 и записью в журнал.
5. Статус внедрения: только `deployed`. Синоним `done` роняет `overall_deploy`.
6. `grade_share` — ступень по грейду (0.0/0.1/0.15/0.2/0.25/0.3), не доля коридора.
7. `except Exception` в `page_team` глотает ошибку и подставляет fallback без
   ключей → `KeyError`. Трейсбек искать в логе, не в HTML-странице.
8. Запускать `python3 -u app.py` — без `-u` лог пуст из-за буферизации.
9. Одноразовые скрипты и применённые патчи — в `_archive/`.

## Как проверить состояние

    bash status.sh      # коды ответов + таблица расчётов
    bash check.sh       # сверка evaluate по всем сотрудникам

## Источник истины

    grading.evaluate(employee, goals)  →  kpi_percent, deploy, letter,
                                          bonus_pct, bonus, grade_name,
                                          grade_share
