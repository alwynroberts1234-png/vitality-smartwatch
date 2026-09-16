# Vitality Watch

Animated watch UI preview with the firmware source kept alongside it.
Opening this project runs **only the desktop UI**. It does not download Zephyr,
west, CMake, Ninja or an ARM SDK, and does not compile or flash firmware.

## Small-download setup

| OS | UI runtime | Additional download |
|---|---|---|
| Windows | Existing Windows .NET Framework compiler and Windows Forms | None when the required Windows components are present |
| Linux | Python 3.10+ with Tk | Only missing Python/Tk packages and their OS dependencies |
| macOS | Python 3.10+ with Tk | None if available; otherwise the matching Python/Tk packages through existing Homebrew |

There are no npm or pip dependencies for the UI. An existing usable runtime is
reused. Package sizes on Linux/macOS depend on what is already installed and on
the package manager; the scripts do not promise a fixed download size.
The preview requires a graphical desktop.

Windows does not need Python, Git, Chocolatey or a firmware toolchain to show the
design. If its .NET Framework compiler is missing, setup reports that prerequisite
instead of downloading a replacement framework.

## Open in VS Code

1. Clone the repository or extract its source ZIP.
2. Choose **File > Open Folder** and select the folder containing this README.
3. Review and trust the folder.
4. Allow automatic tasks if prompted.
5. Run **Tasks: Run Task > Vitality: Open project**, or reopen the folder.

The startup sequence in [.vscode/tasks.json](.vscode/tasks.json) is:

1. **Detect OS**.
2. **Check UI environment** without installing anything.
3. **Prepare UI environment**. Reuse existing tools; install missing Python/Tk
   packages on Linux/macOS only.
4. **Show watch design**. Windows builds the desktop preview executable locally
   when needed. Linux/macOS run the Python preview directly.

A failed stage stops subsequent stages. There is no firmware build task.
On later opens, setup reuses the UI runtime. An already running preview is reused
instead of opening duplicate windows. On Linux/macOS, the task stays active while
the preview window is open.

If you previously clicked **Don't Allow**, open the Command Palette
(**Ctrl+Shift+P**, or **Cmd+Shift+P** on macOS), run **Tasks: Manage Automatic
Tasks**, choose **Allow Automatic Tasks**, then run **Developer: Reload Window**.
The folder must also be trusted. See the official
[task documentation](https://code.visualstudio.com/docs/debugtest/tasks#_control-automatic-task-execution).

To disable automatic startup, set `task.allowAutomaticTasks` to `off` in
[.vscode/settings.json](.vscode/settings.json). To reopen only the UI, use
**Tasks: Run Task > Vitality: Start preview**.

## Run from a terminal

Run these commands from the repository root.

Windows: check the existing runtime, build the desktop preview if needed, and open it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1
```

Linux/macOS: prepare only the UI runtime, then open the preview:

```sh
bash tools/setup-host.sh
```

To inspect the plan without downloading or launching anything:

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1 -Plan
```

```sh
# Linux/macOS
bash tools/setup-host.sh --plan
```

To launch the UI directly, without installing dependencies:

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Preview.ps1 -Run
```

```sh
# Linux/macOS, with a usable Python/Tk runtime
bash tools/run-dev.sh preview
# Or with your selected Python:
python3 preview/watch_preview.py
```

After its first successful build, the Windows preview is available at
`build/VitalityPreview.exe`.

## Linux and macOS runtime setup

The setup script first searches for Python 3.10+ that can import Tk.
Set `VITALITY_PREVIEW_PYTHON` to a suitable executable to prefer your installation:

```sh
export VITALITY_PREVIEW_PYTHON="/path/to/python3"
bash tools/setup-host.sh
```

The chosen executable path is saved in the ignored `.tools/preview-python` file.
No new virtual environment is created.

If Python/Tk is missing, Linux setup uses apt, dnf or pacman and may request your
sudo password. macOS setup uses an existing [Homebrew](https://brew.sh/) to install
`python-tk@3.12` and its matching Python dependencies. If Homebrew is absent,
install a Python distribution with Tk or install Homebrew yourself, then retry.
Existing package managers are used; the project does not install them.

## Using the watch UI

Select screens and themes with the preview controls. Use arrows/swipes to
navigate and the crown or Space to sleep/wake. Heart Rate and Activity provide
simulated measurements and workout actions.

The UI animates rings, hearts, traces and clock hands. The Windows renderer also
has theme effects and transitions. The portable Tk renderer uses the same themes
but is not pixel-identical. Neither preview executes the firmware or simulates
the watch hardware.

## Troubleshooting

| Symptom | Action |
|---|---|
| Nothing runs when opening VS Code | Open the whole folder, check trust and automatic-task permissions, then run `Vitality: Open project`. |
| Windows reports a missing .NET Framework compiler | Restore/install the required Windows .NET Framework components, then retry. |
| Python/Tk cannot be found | Run the setup task, or set `VITALITY_PREVIEW_PYTHON` to a Python 3.10+ executable with Tk. |
| Package installation fails | Check the terminal error, internet access and package-manager permissions; retry setup after correcting it. |
| UI does not appear on Linux/macOS | Read the task terminal and check that your session has a graphical display. Remote/headless sessions need a display. |
| Windows preview cannot be replaced | Close its window and rerun `Vitality: Start preview`. |

## Firmware source

The C firmware, headers, board configuration, Zephyr manifest and assets remain
in the repository for maintenance. They are excluded from the UI startup flow.
The previous automatic firmware environment downloader has been removed.

The baseline is Zephyr v4.1.0 with its pinned LVGL module. The default target is a
headless nRF52840 DK with simulated sensor data. Custom watch support still needs
the actual display controller, board pin map and power integration.

Manual firmware build helpers are retained for future development with a
separately configured toolchain. UI setup does not prepare that toolchain.
A real Zephyr target build and hardware tests remain unverified.

See [hardware requirements](docs/HARDWARE.md),
[board integration](boards/vitality/README.md), and
[architecture](docs/ARCHITECTURE.md).

## Optional asset checks and tests

These commands are manual development checks, not part of opening the UI.

Windows asset generation and preview render checks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Assets.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Preview.ps1 -Render
```

SVG masters live under `assets/masters`. The optional asset pack is written to
`qspi_image/output`; render checks write to `build/screenshots`.

Launcher and preview tests, using an existing Python installation:

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

These tests do not install dependencies or cross-compile firmware. Firmware
launcher tests mock their compiler commands. Native Linux/macOS setup tests run
on those platforms in CI; they have not been executed locally on Windows.

## Project map

- `preview/`: animated desktop UI.
- `assets/masters/`: curated SVG artwork.
- `vitality_watch_assets/`: supplied theme and animation data.
- `.vscode/`, `tools/`: UI startup, optional development helpers and tests.
- `src/`, `include/`: firmware source.
- `boards/`, `config/`, `qspi_image/`: hardware and asset integration.
- `docs/`: [setup details](docs/VSCODE.md), architecture and
  [verification status](docs/VERIFICATION.md).

The original specification is in [PROJECT_SPEC.md](PROJECT_SPEC.md).
