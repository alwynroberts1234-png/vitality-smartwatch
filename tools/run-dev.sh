#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$root/.tools/venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  printf '%s\n' 'Run Vitality: Open project once to prepare the environment.' >&2
  exit 1
fi
exec "$python_bin" "$root/tools/dev.py" "${1:-firmware}"
