#!/usr/bin/env bash
# Abre o AniLauncher. Detecta o Python 3 disponível.
set -euo pipefail
cd "$(dirname "$0")"

for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" anilauncher.py "$@"
  fi
done

echo "Python 3 não encontrado. Instale com: sudo apt install python3 python3-tk" >&2
exit 1
