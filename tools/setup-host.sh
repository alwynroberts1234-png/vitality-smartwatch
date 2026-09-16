#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
stage="${1:-all}"
if [[ "$stage" == --plan ]]; then
  printf '%s\n' 'UI only: detect OS, find Python 3.10+ with Tk, install missing UI packages, then show the watch.' \
    'Reuse an existing runtime. No pip packages, virtual environment or firmware toolchain downloads.'
  exit 0
fi
case "$stage" in all|--detect|--check|--download|--launch) ;;
  *) printf '%s\n' "Unknown setup stage: $stage" >&2; exit 1 ;;
esac
host="$(uname -s)"
case "$host" in
  Darwin) host_name=macOS ;;
  Linux) host_name=Linux ;;
  *) printf '%s\n' 'Use Setup-Environment.ps1 on Windows.' >&2; exit 1 ;;
esac
if [[ "$stage" == all || "$stage" == --detect ]]; then
  printf '%s\n' "[1/4] OS detected: $host_name"
  if [[ "$stage" == --detect ]]; then exit 0; fi
fi
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
runtime_file="$root/.tools/preview-python"
python_bin=""
find_python() {
  local candidate
  local candidates=()
  if [[ -n "${VITALITY_PREVIEW_PYTHON:-}" ]]; then
    candidates+=("$VITALITY_PREVIEW_PYTHON")
  fi
  if [[ -f "$runtime_file" ]]; then candidates+=("$(cat "$runtime_file")"); fi
  candidates+=(python3 python3.12 python3.11
    /opt/homebrew/opt/python@3.12/bin/python3.12
    /usr/local/opt/python@3.12/bin/python3.12
    "$root/.tools/venv/bin/python")
  for candidate in "${candidates[@]}"; do
    if "$candidate" -c 'import sys, tkinter; assert sys.version_info >= (3,10)' >/dev/null 2>&1; then
      python_bin="$(command -v "$candidate")"
      return 0
    fi
  done
  return 1
}
if [[ "$stage" == all || "$stage" == --check ]]; then
  printf '%s\n' '[2/4] Check UI environment'
  if find_python; then printf '%s\n' "Python/Tk ready: $python_bin"
  else printf '%s\n' 'Python 3.10+ with Tk is missing; UI runtime setup is needed.'; fi
  if [[ "$stage" == --check ]]; then exit 0; fi
fi
if [[ "$stage" == all || "$stage" == --download ]]; then
  printf '%s\n' '[3/4] Prepare UI environment'
  if ! find_python; then
    if [[ "$host" == Darwin ]]; then
      if ! command -v brew >/dev/null; then
        printf '%s\n' 'Install Python 3.10+ with Tk, or Homebrew from https://brew.sh, then rerun.' >&2
        exit 1
      fi
      # This formula brings its matching Python only when needed.
      brew install python-tk@3.12
    else
      elevate=()
      if [[ "$(id -u)" != 0 ]]; then elevate=(sudo); fi
      if command -v apt-get >/dev/null; then
        "${elevate[@]}" apt-get update
        "${elevate[@]}" apt-get install -y --no-install-recommends python3-tk
      elif command -v dnf >/dev/null; then
        "${elevate[@]}" dnf install -y python3-tkinter
      elif command -v pacman >/dev/null; then
        "${elevate[@]}" pacman -S --needed python tk
      else
        printf '%s\n' 'Install Python 3.10+ with Tk using your OS package manager.' >&2
        exit 1
      fi
    fi
    if ! find_python; then
      printf '%s\n' 'A usable Python/Tk runtime was not found. Set VITALITY_PREVIEW_PYTHON to its executable.' >&2
      exit 1
    fi
  else
    printf '%s\n' 'Using existing Python/Tk. Download size: 0 bytes.'
  fi
  mkdir -p "$root/.tools"
  printf '%s\n' "$python_bin" > "$runtime_file"
  if [[ "$stage" == --download ]]; then exit 0; fi
fi
printf '%s\n' '[4/4] Show watch design'
if ! find_python; then
  printf '%s\n' 'Run Vitality: Open project to prepare the UI runtime first.' >&2
  exit 1
fi
exec "$python_bin" "$root/preview/watch_preview.py"
