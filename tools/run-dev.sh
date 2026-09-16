#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-preview}" == preview ]]; then
  exec bash "$root/tools/setup-host.sh" --launch
fi
# Optional manual firmware commands require an environment supplied by the developer.
python_bin="${VITALITY_ZEPHYR_PYTHON:-python3}"
exec "$python_bin" "$root/tools/dev.py" "$@"
