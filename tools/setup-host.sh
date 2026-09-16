#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "${1:-}" == "--plan" ]]; then
  printf '%s\n' 'Install missing host tools using an EXISTING package manager.' \
    'Create .tools/venv; fetch Zephyr v4.1.0; install the ARM SDK; launch UI and compile.' \
    'Plan only: no changes. A package manager and administrator rights may be required.'
  exit 0
fi
stage="${1:-all}"
case "$stage" in
  --detect)
    case "$(uname -s)" in
      Darwin) printf '%s\n' '[1/4] OS detected: macOS' ;;
      Linux) printf '%s\n' '[1/4] OS detected: Linux' ;;
      *) printf '%s\n' 'Unsupported host; use Setup-Environment.ps1 on Windows.' >&2; exit 1 ;;
    esac
    exit 0 ;;
  --launch)
    printf '%s\n' '[4/4] Compile firmware and show design'
    if [[ ! -x "$root/.tools/venv/bin/python" ]]; then
      printf '%s\n' 'Environment missing. Run Vitality: Open project first.' >&2; exit 1
    fi
    exec "$root/.tools/venv/bin/python" "$root/tools/setup_env.py" --launch-only ;;
  all|--check|--download) ;;
  *) printf '%s\n' "Unknown setup stage: $stage" >&2; exit 1 ;;
esac
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
python_bin="${VITALITY_BOOTSTRAP_PYTHON:-python3}"
if [[ -z "${VITALITY_BOOTSTRAP_PYTHON:-}" && -x "$root/.tools/venv/bin/python" ]]; then
  python_bin="$root/.tools/venv/bin/python"
fi
missing=0
for tool in git gperf dtc wget; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf '%s\n' "Missing host tool: $tool"
    missing=1
  fi
done
python_ready=1
"$python_bin" -c 'import sys, venv, tkinter; assert sys.version_info >= (3,10)' >/dev/null 2>&1 || python_ready=0
if [[ "$python_ready" == 0 ]]; then missing=1; printf '%s\n' 'Missing usable Python 3.10+ with Tk/venv.'; fi
if [[ "$stage" == --check ]]; then
  printf '%s\n' '[2/4] Check development environment (no installation)'
  if [[ "$missing" == 0 ]]; then printf '%s\n' 'Host prerequisites found.'; fi
  if [[ "$python_ready" == 1 ]]; then
    exec "$python_bin" "$root/tools/setup_env.py" --check
  fi
  printf '%s\n' 'Environment needs preparation; continuing to the download stage.'
  exit 0
fi
printf '%s\n' '[3/4] Download and prepare missing development tools'
if [[ "$missing" == 1 ]]; then
  case "$(uname -s)" in
    Darwin)
      if ! command -v brew >/dev/null; then
        printf '%s\n' 'Homebrew is missing. Install it from https://brew.sh, then rerun this task.' >&2; exit 1
      fi
      brew install git gperf dtc wget python@3.12 python-tk@3.12
      python_bin="$(brew --prefix python@3.12)/bin/python3.12"
      ;;
    Linux)
      elevate=()
      if [[ "$(id -u)" != 0 ]]; then elevate=(sudo); fi
      if command -v apt-get >/dev/null; then
        "${elevate[@]}" apt-get update
        "${elevate[@]}" apt-get install -y --no-install-recommends git gperf device-tree-compiler wget \
          python3 python3-venv python3-pip python3-tk xz-utils file unzip
      elif command -v dnf >/dev/null; then
        "${elevate[@]}" dnf install -y git gperf dtc wget python3 python3-pip python3-tkinter xz file unzip
      elif command -v pacman >/dev/null; then
        "${elevate[@]}" pacman -S --needed git gperf dtc wget python python-pip tk xz file unzip
      else
        printf '%s\n' 'Install Python/Tk, Git, gperf, dtc and wget using your system package manager.' >&2; exit 1
      fi
      ;;
    *) printf '%s\n' 'Use Setup-Environment.ps1 on Windows.' >&2; exit 1 ;;
  esac
fi
for tool in git gperf dtc wget; do command -v "$tool" >/dev/null; done
"$python_bin" -c 'import sys, venv, tkinter; assert sys.version_info >= (3,10)'
if [[ "$stage" == --download ]]; then
  exec "$python_bin" "$root/tools/setup_env.py"
fi
exec "$python_bin" "$root/tools/setup_env.py" --start
