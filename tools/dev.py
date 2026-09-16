"""Portable Zephyr build and Tk preview launcher. No third-party Python packages."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def venv_python(folder: Path, platform: str = sys.platform) -> Path:
    return folder / ("Scripts/python.exe" if platform == "win32" else "bin/python")


def firmware_config(args, root=ROOT, environ=None, platform=sys.platform):
    env = dict(os.environ if environ is None else environ)
    try:
        state = json.loads((root / ".tools" / "environment.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if state.get("root") != str(root):
        state = {}
    env["PATH"] = os.pathsep.join(state.get("path_entries", []) + [env.get("PATH", "")])
    if state.get("sdk"):
        env.setdefault("ZEPHYR_SDK_INSTALL_DIR", state["sdk"])
        env.setdefault("ZEPHYR_TOOLCHAIN_VARIANT", "zephyr")
    workspace = Path(args.workspace or env.get("VITALITY_ZEPHYR_WORKSPACE")
                     or state.get("workspace")
                     or root.parent / "zephyr-workspace").expanduser().resolve()
    selected = args.python or env.get("VITALITY_ZEPHYR_PYTHON") or state.get("python")
    if selected:
        interpreter = Path(shutil.which(selected, path=env.get("PATH")) or selected).expanduser().absolute()
    else:
        candidates = [venv_python(root.parent / "zephyr-env", platform)]
        if env.get("VIRTUAL_ENV"):
            candidates.append(venv_python(Path(env["VIRTUAL_ENV"]), platform))
        candidates.append(Path(sys.executable))
        interpreter = next((p for p in candidates if p.is_file()), candidates[0])
    if not interpreter.is_file():
        raise RuntimeError("Python environment not found: " + str(interpreter))
    base = workspace / "zephyr"
    if not (workspace / ".west").is_dir() or not (base / "CMakeLists.txt").is_file():
        raise RuntimeError("Zephyr workspace not found: " + str(workspace) +
                           ". Set VITALITY_ZEPHYR_WORKSPACE. See docs/VSCODE.md.")
    env["PATH"] = str(interpreter.parent) + os.pathsep + env.get("PATH", "")
    env["ZEPHYR_BASE"] = str(base)
    return workspace, interpreter, env


def firmware(args, root=ROOT):
    workspace, interpreter, env = firmware_config(args, root)
    result = subprocess.run([str(interpreter), "-m", "west", "--version"], cwd=workspace, env=env)
    if result.returncode:
        raise RuntimeError("west is not installed in " + str(interpreter))
    for tool in ("cmake", "ninja"):
        if not shutil.which(tool, path=env["PATH"]):
            raise RuntimeError(tool + " is missing from PATH. Install Zephyr prerequisites and restart VS Code.")
    if args.action == "check":
        print("Build tools found; the actual build will verify SDK compatibility.", flush=True)
        return 0
    build = root / "build" / "firmware"
    extra = ""
    if args.extra_conf:
        config = Path(args.extra_conf).expanduser()
        if not config.is_absolute():
            config = root / config
        if not config.is_file():
            raise RuntimeError("Configuration not found: " + str(config))
        extra = str(config.resolve())
    command = [str(interpreter), "-m", "west", "build", "-p", "auto",
               "-b", args.board, str(root), "-d", str(build),
               "--", "-DVITALITY_HOST_TESTS=OFF", "-DEXTRA_CONF_FILE=" + extra]
    print("Compiling firmware for " + args.board, flush=True)
    result = subprocess.run(command, cwd=workspace, env=env)
    if result.returncode:
        raise RuntimeError("west build failed with exit code " + str(result.returncode))
    elf = build / "zephyr" / "zephyr.elf"
    if not elf.is_file():
        raise RuntimeError("Build returned without output: " + str(elf))
    print("Firmware built: " + str(elf), flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("firmware", "check", "preview"))
    parser.add_argument("--workspace")
    parser.add_argument("--python")
    parser.add_argument("--board", default="nrf52840dk/nrf52840")
    parser.add_argument("--extra-conf")
    args = parser.parse_args(argv)
    try:
        if args.action == "preview":
            # Use the interpreter that launched this task; no environment activation required.
            script = ROOT / "preview" / "watch_preview.py"
            old = sys.argv
            try:
                sys.argv = [str(script)]
                runpy.run_path(str(script), run_name="__main__")
            finally:
                sys.argv = old
            return 0
        return firmware(args)
    except (RuntimeError, OSError) as error:
        print("VITALITY: " + str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
