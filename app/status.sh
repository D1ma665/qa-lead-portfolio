#!/usr/bin/env bash
# status.sh — состояние приложения: страницы, лог, сводка расчёта.
# Запуск из любой папки: cd "$(dirname "$0")" ниже.
cd "$(dirname "$0")"

echo "## $(date '+%Y-%m-%d %H:%M')"
echo

echo "### Страницы"
for p in / /team /scores /matrix; do
  printf "%-9s %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080$p)"
done
echo

echo "### Ошибки в логе"
grep -v "^QA Stage" /tmp/app.log 2>/dev/null | tail -10 || true
echo

echo "### Расчёт"
python3 - << 'PYEOF'
import json
import grading
import grading_compat as gc

with open('state.json', encoding='utf-8') as f:
    d = json.load(f)

hdr = (f'{"ФИО":<20}{"грейд":<9}{"src":<9}{"shr":>5}'
       f'{"б":>3}{"КПИ":>8}{"анкета%":>9}{"премия%":>9}{"руб":>10}')
print(hdr)
print('-' * len(hdr))

for e in d['employees']:
    r = grading.evaluate(e, gc._goals_for(e))
    name = (e.get('name') or '')[:19]
    grade = r.get('grade') or '—'
    src = r.get('grade_source') or '—'
    shr = str(r.get('grade_share'))
    letter = str(r.get('letter') or '—')
    kpi = r.get('kpi_percent')
    kpi = '—' if kpi is None else f'{kpi:.1f}'
    fill = r.get('fill_percent')
    fill = '—' if fill is None else f'{fill:.1f}'
    bpct = r.get('bonus_pct')
    bpct = '—' if bpct is None else f'{bpct:.1f}'
    rub = r.get('bonus') or 0
    print(f'{name:<20}{grade:<9}{src:<9}{shr:>5}'
          f'{letter:>3}{kpi:>8}{fill:>9}{bpct:>9}{rub:>10.0f}')

print()
print('src: scores — из оценок, period — из прошлого периода, default — оценок не было')
print('премия 0 при src=default или анкета <= 90% (требования §4.4.3, §4.5.5)')
PYEOF
