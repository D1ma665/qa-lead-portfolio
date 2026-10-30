#!/usr/bin/env bash
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
import json, grading, grading_compat as gc
d = json.load(open('state.json'))
print(f'{"ФИО":<20}{"грейд":<9}{"shr":>5}{"б":>3}{"КПИ":>8}{"премия%":>8}{"руб":>10}')
for e in d['employees']:
    r = grading.evaluate(e, gc._goals_for(e))
    grade = r.get('grade') or '—'
    print(f"{e['name'][:19]:<20}{grade:<9}{str(r.get('grade_share')):>5}"
          f"{str(r.get('letter')):>3}{str(r.get('kpi_percent')):>8}"
          f"{str(r.get('bonus_pct')):>8}{str(r.get('bonus')):>10}")
PYEOF
