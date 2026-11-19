#!/usr/bin/env bash
# Revisa lo que vas a commitear de lectucli con el subagente revisor (solo lectura), sin abrir la TUI.
# Uso: git add … && scripts/revisar.sh      (sale con 0 si el revisor dice OK)
set -euo pipefail
if git diff --staged --quiet; then
  echo "No hay nada preparado: haz git add primero." >&2
  exit 1
fi
revision=$(git diff --staged | timeout 180 opencode run --agent revisor \
  "Revisa este diff (te llega por la entrada estándar) con tus normas. Acaba con una línea: VEREDICTO: OK o VEREDICTO: CAMBIAR.")
echo "$revision"
grep -q "^VEREDICTO: OK" <<< "$revision"
