#!/bin/sh
# Проверка битых относительных ссылок во всех .md репозитория
# Запуск: sh check-links.sh

cd "$(dirname "$0")" || exit 1

find . -name "*.md" -not -path "./.git/*" -not -path "./app/*" \
  | while read -r f; do
      d=$(dirname "$f")
      sed -n 's/.*](\([^)#][^)]*\)).*/\1/p' "$f" \
        | grep -v '^http' \
        | grep -v '^mailto:' \
        | while read -r p; do
            case "$p" in /*) continue ;; esac
            [ -e "$d/$p" ] || echo "❌ $f → $p"
          done
    done

echo "--- проверка завершена ---"
