from nicegui import ui
import pandas as pd

from config import APP_NAME, VERSION, COMPS, GRADES, PPL, MARK_K, MARK_LABEL
from grading import build_results, comp_pct
from export_excel import export
from state import STATE, save


def results_df():
    return pd.DataFrame(build_results(
        people=PPL,
        history=STATE['history'],
        bases=STATE['bases'],
        goals=STATE['goals'],
        scores=STATE['scores'],
    ))


def fmt_rub(x):
    return format(int(round(x)), ',').replace(',', chr(32))

def nav():
    with ui.row().classes('fixed bottom-0 left-0 w-full bg-white shadow-2 justify-center gap-2 p-2'):
        ui.button('Дашборд', on_click=lambda: ui.navigate.to('/')).props('flat')
        ui.button('Команда', on_click=lambda: ui.navigate.to('/team')).props('flat')
        ui.button('Оценки', on_click=lambda: ui.navigate.to('/scores')).props('flat')
        ui.button('Цели', on_click=lambda: ui.navigate.to('/goals')).props('flat')
        ui.button('Премия', on_click=lambda: ui.navigate.to('/salary')).props('flat')
        ui.button('Экспорт', on_click=lambda: ui.navigate.to('/export')).props('flat')


def header(title, subtitle=None):
    with ui.header().classes('bg-blue-9'):
        ui.label(title).classes('text-h6 font-bold')
        if subtitle:
            ui.label(subtitle).classes('text-caption opacity-70 ml-2')


def metric_card(caption, value, color='text-blue-9'):
    with ui.card().classes('w-56'):
        ui.label(caption).classes('text-caption text-grey-7')
        ui.label(value).classes('text-h4 font-bold ' + color)


@ui.page('/')
def page_dashboard():
    header(APP_NAME, VERSION)
    df = results_df()

    with ui.column().classes('p-4 w-full max-w-6xl mx-auto gap-4 pb-20'):
        ui.label('ГРЕЙД <- компетенции | ОЦЕНКА <- цели | ПРЕМИЯ = оклад x %грейд x коэф').classes('text-caption text-grey-7')

        with ui.row().classes('gap-4'):
            metric_card('Средний % компетенций', format(df['% компетенций'].mean(), '.1f'))
            metric_card('Фонд премий, руб.', fmt_rub(df['Премия'].sum()), 'text-green-8')
            metric_card('Сотрудников', str(len(df)), 'text-black')

        ui.label('Команда').classes('text-h6 mt-2')
        show_cols = ['Сотрудник', '% компетенций', 'Грейд', 'Оценка', 'Премия', 'Статус']
        ui.table.from_pandas(df[show_cols], row_key='Сотрудник').classes('w-full')

        with ui.row().classes('gap-4 w-full'):
            with ui.card().classes('flex-1'):
                ui.label('Распределение по грейдам').classes('text-subtitle1')
                dist = df['Грейд'].value_counts().rename_axis('Грейд').reset_index(name='Кол-во')
                ui.table.from_pandas(dist, row_key='Грейд').classes('w-full')

            with ui.card().classes('flex-1'):
                ui.label('Премии по сотрудникам').classes('text-subtitle1')
                ui.echart({
                    'xAxis': {'type': 'category', 'data': df['Сотрудник'].tolist()},
                    'yAxis': {'type': 'value'},
                    'series': [{'type': 'bar', 'data': df['Премия'].tolist()}],
                    'grid': {'containLabel': True},
                }).classes('h-64 w-full')

    nav()

@ui.page('/goals')
def page_goals():
    header('Цели -> Оценка A-E')

    with ui.column().classes('p-4 w-full max-w-6xl mx-auto gap-4 pb-20'):

        @ui.refreshable
        def goals_table():
            gdf = pd.DataFrame(STATE['goals']).rename(columns={
                'person': 'Сотрудник', 'goal': 'Цель', 'c': 'Ц.',
                'pct': '% вып.', 'over': 'Перевыполнил'})
            ui.table.from_pandas(gdf).classes('w-full')

        goals_table()

        ui.label('Добавить цель').classes('text-h6 mt-4')
        with ui.card().classes('w-full'):
            with ui.row().classes('gap-4'):
                p = ui.select(PPL, value=PPL[0], label='Сотрудник').classes('w-56')
                goal = ui.input('Цель').classes('flex-1')
                cc = ui.select(['Ц1', 'Ц2', 'Ц3'], value='Ц1', label='Привязка').classes('w-32')
            with ui.row().classes('gap-4 items-center'):
                pct = ui.slider(min=0, max=150, value=100).classes('flex-1')
                over = ui.checkbox('Перевыполнил (инструмент автоматизации)')

            def add():
                if not goal.value:
                    ui.notify('Введи название цели', type='warning')
                    return
                STATE['goals'].append({'person': p.value, 'goal': goal.value,
                                       'c': cc.value, 'pct': int(pct.value),
                                       'over': over.value})
                save(STATE)
                ui.notify('Цель добавлена', type='positive')
                goal.value = ''
                goals_table.refresh()
                calc_table.refresh()

            ui.button('Добавить', on_click=add).props('color=primary')

        ui.label('Расчётная оценка').classes('text-h6 mt-4')

        @ui.refreshable
        def calc_table():
            df = results_df()[['Сотрудник', '% цели', 'Оценка', 'Смысл']]
            ui.table.from_pandas(df, row_key='Сотрудник').classes('w-full')

        calc_table()

    nav()


@ui.page('/salary')
def page_salary():
    header('Калькулятор премии')

    with ui.column().classes('p-4 w-full max-w-3xl mx-auto gap-4 pb-20'):
        ui.label('Меняй оклад или грейд - премия пересчитается на лету.').classes('text-caption text-grey-7')

        with ui.card().classes('w-full'):
            person = ui.select(PPL, value=PPL[0], label='Сотрудник').classes('w-64')
            base = ui.number('Оклад, руб.', step=5000, format='%.0f').classes('w-64')

            grade_opts = {}
            for gidx, g in enumerate(GRADES):
                grade_opts[g[0] + ' (' + str(int(g[2] * 100)) + '%)'] = gidx
            pc = ui.select(grade_opts, label='Грейд (доля премии)').classes('w-64')

            mark_opts = {}
            for m in MARK_K:
                mark_opts[m + ' - ' + MARK_LABEL[m]] = m
            coef = ui.select(mark_opts, label='Оценка').classes('w-64')

            result = ui.label().classes('text-h4 font-bold text-green-8 mt-4')

            def recalc():
                gidx = pc.value if pc.value is not None else -1
                pcv = GRADES[gidx][2] if gidx is not None and gidx >= 0 else 0.0
                mk = coef.value
                prem = round((base.value or 0) * pcv * MARK_K.get(mk, 0))
                result.text = 'Премия: ' + fmt_rub(prem) + ' руб.'

            def load(p):
                df = results_df()
                r = df[df['Сотрудник'] == p]
                if r.empty:
                    return
                r = r.iloc[0]
                base.value = int(STATE['bases'].get(p, 0))
                pc.value = int(r['gidx']) if int(r['gidx']) >= 0 else None
                coef.value = r['Оценка']
                recalc()

            def save_base():
                STATE['bases'][person.value] = int(base.value or 0)
                save(STATE)
                ui.notify('Оклад сохранён', type='positive')

            person.on_value_change(lambda e: load(e.value))
            base.on_value_change(lambda: recalc())
            pc.on_value_change(lambda: recalc())
            coef.on_value_change(lambda: recalc())

            load(PPL[0])

            with ui.row():
                ui.button('Сохранить оклад', on_click=save_base).props('color=primary')

            ui.code('ПРЕМИЯ = оклад x %премии(грейд) x коэффициент(оценка)')

    nav()


@ui.page('/export')
def page_export():
    header('Экспорт в Excel')

    with ui.column().classes('p-4 w-full max-w-3xl mx-auto gap-4 pb-20'):
        status = ui.label()

        def do_export():
            path = export('QA_System.xlsx',
                          results=build_results(
                              people=PPL, history=STATE['history'],
                              bases=STATE['bases'], goals=STATE['goals'],
                              scores=STATE['scores']),
                          scores=STATE['scores'],
                          goals=STATE['goals'])
            status.text = 'Файл готов: ' + path
            ui.notify('Excel сформирован', type='positive')

        ui.button('Сформировать QA_System.xlsx', on_click=do_export).props('color=primary')
        ui.label('Файл появится рядом с app.py').classes('text-caption text-grey-7')

    nav()


@ui.page('/team')
def page_team():
    header('Команда')
    df = results_df()
    with ui.column().classes('p-4 w-full max-w-6xl mx-auto gap-4 pb-20'):
        ui.table.from_pandas(df, row_key='Сотрудник').classes('w-full')
        ui.label('История по кварталам').classes('text-h6 mt-4')
        rows = []
        for p in PPL:
            d = {'Сотрудник': p}
            for i, v in enumerate(STATE['history'].get(p, [])):
                d['Q' + str(i + 1)] = v
            d['Максимум'] = max(STATE['history'].get(p, []) or [0])
            rows.append(d)
        ui.table.from_pandas(pd.DataFrame(rows), row_key='Сотрудник').classes('w-full')
    nav()

@ui.page('/scores')
def page_scores():
    header('Оценка компетенций', 'влияет на грейд')
    with ui.column().classes('p-4 w-full max-w-6xl mx-auto gap-4 pb-20'):
        ui.label('Балл 1-5. В грейд идут только ДА.').classes('text-caption text-grey-7')
        person = ui.select(PPL, value=PPL[0], label='Сотрудник').classes('w-64')
        calc_label = ui.label().classes('text-h6 text-blue-9')
        sliders = {}

        def refresh_calc():
            calc_label.text = 'Текущий % компетенций: ' + format(comp_pct(STATE['scores'][person.value]), '.2f')

        @ui.refreshable
        def editors():
            sliders.clear()
            row = STATE['scores'][person.value]
            for i, comp in enumerate(COMPS):
                name, cat, prio, w, ing = comp
                with ui.row().classes('items-center gap-4 w-full'):
                    mark = '*' if ing == chr(1044) + chr(1040) else '-'
                    ui.label(mark + ' ' + name + ' (' + cat + ', вес ' + str(w) + ')').classes('w-96 text-sm')
                    sliders[i] = ui.slider(min=1, max=5, step=1, value=int(row[i])).classes('flex-1')
            refresh_calc()

        person.on_value_change(lambda: editors.refresh())
        with ui.card().classes('w-full'):
            editors()

        def do_save():
            STATE['scores'][person.value] = [int(sliders[i].value) for i in range(len(COMPS))]
            save(STATE)
            refresh_calc()
            ui.notify('Баллы сохранены: ' + person.value, type='positive')

        def do_reset():
            from config import SCORES as DEF
            STATE['scores'][person.value] = list(DEF[person.value])
            save(STATE)
            editors.refresh()
            ui.notify('Сброшено к config', type='info')

        with ui.row():
            ui.button('Сохранить', on_click=do_save).props('color=primary')
            ui.button('Сбросить', on_click=do_reset).props('flat')

        ui.label('Текущая матрица оценок').classes('text-h6 mt-4')
        data = []
        for i in range(len(COMPS)):
            data.append([COMPS[i][0]] + [STATE['scores'][p][i] for p in PPL])
        ui.table.from_pandas(pd.DataFrame(data, columns=['Компетенция'] + PPL), row_key='Компетенция').classes('w-full')
    nav()

ui.run(title=APP_NAME, dark=False, reload=False, host='0.0.0.0', port=8080)