# Vitality Watch

Firmware foundation with Windows and portable Python/Tk desktop previews, based on your
assets.png, supplied asset ZIP and watch specification.

## First-time setup

The setup scripts prepare **Zephyr v4.1.0 and an ARM SDK**, open the animated watch
preview, and compile firmware for `nrf52840dk/nrf52840`.

Full first-time installation and a real Zephyr cross-build have **not yet been
verified**. The desktop preview and launcher tests have been checked locally on
Windows. The firmware is a headless development-kit foundation; running the UI on
your watch hardware still requires its board and display integration.

### 1. Prepare your computer

Use local desktop VS Code, an internet connection, and several GB of free disk
space. Firmware dependencies are substantial downloads. A local graphical desktop
is required for the preview.

| OS | Required before automatic setup | What setup installs when missing |
|---|---|---|
| Windows | PowerShell and [Chocolatey](https://chocolatey.org/install); administrator rights may be needed for host packages | Python, Git, gperf, dtc, wget and 7zip |
| macOS | Bash and [Homebrew](https://brew.sh/) | Python/Tk, Git, gperf, dtc and wget |
| Linux | Bash and apt, dnf or pacman; sudo access for host packages | Python/Tk, Git and other host build utilities |

Install a missing package manager using its linked official instructions. The
repository does not install Chocolatey or Homebrew for you. If all host tools are
already installed, the scripts skip package-manager installation steps.

On Windows, if Chocolatey reports that elevation is required, install the host
packages in an administrator PowerShell terminal, then return to normal VS Code:

```powershell
choco install python311 git gperf dtc-msys2 wget 7zip -y
```

### 2. Open the repository folder

1. Clone this repository, or download and extract its source ZIP.
2. In VS Code, select **File > Open Folder** and choose the folder containing
   this README.
3. Review the repository and trust the folder when prompted. Tasks cannot run in
   Restricted Mode.
4. If automatic tasks are blocked, run **Tasks: Manage Automatic Tasks** from the
   Command Palette and allow them for this folder.
5. Run **Tasks: Run Task > Vitality: Open project** to start immediately, or reopen
   the folder to trigger startup automatically.

The repository enables automatic tasks in `.vscode/settings.json`. Workspace
trust and organization policies still apply. See the official
[task documentation](https://code.visualstudio.com/docs/debugtest/tasks#_run-behavior)
and [Workspace Trust guide](https://code.visualstudio.com/docs/editing/workspaces/workspace-trust).

### 3. Wait for setup and compilation

The **Vitality: Open project** terminal shows progress in this order:

1. Check host tools and install missing prerequisites.
2. Create `.tools/venv` and install west, CMake and Ninja.
3. Fetch Zephyr v4.1.0 and its modules, then install its Python requirements.
4. Find or install the compatible ARM SDK and save environment paths.
5. Open the animated preview and start the firmware build.

Successful compilation reports `Firmware built:` and creates
`build/firmware/zephyr/zephyr.elf`. These tasks do not flash a device. The desktop
UI runs independently of the firmware build.

Subsequent opens reuse the saved environment and build incrementally. A setup
failure stops startup before launching the UI; a later firmware compilation
failure leaves the preview open.

## Everyday use

| Action | VS Code command |
|---|---|
| Set up tools, open UI and build firmware | Tasks: Run Task > Vitality: Open project |
| Build firmware again | Tasks: Run Build Task; Ctrl+Shift+B on Windows/Linux, Cmd+Shift+B on macOS |
| Open the UI separately | Tasks: Run Task > Vitality: Start preview |
| Disable automatic startup | Set `task.allowAutomaticTasks` to `off` in `.vscode/settings.json` |

## Setup from a terminal

Run all commands below from the repository root. These commands perform the same
setup, UI launch and build as the folder-open task.

Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1
```

Linux/macOS:

```sh
bash tools/setup-host.sh
```

To inspect the setup plan without installing anything:

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1 -Plan
```

```sh
# Linux/macOS
bash tools/setup-host.sh --plan
```

Setup normally stores its environment in the ignored `.tools` directory. It also
supports an existing Zephyr 4.1.0 workspace. See [advanced setup and environment
overrides](docs/VSCODE.md#existing-environments-and-manual-commands).

## Troubleshooting setup

| Symptom | What to do |
|---|---|
| Nothing happens when opening VS Code | Open the whole repository folder, check Workspace Trust and automatic-task permissions, then run `Vitality: Open project` manually. |
| Chocolatey or Homebrew is missing | Install the package manager from its official site above, then retry. |
| Host installation fails with a permissions error | On Windows, install host prerequisites in an administrator terminal. On Linux, supply the sudo password when requested. |
| Download or package installation fails | Check connectivity and available storage, fix the reported error, then rerun `Vitality: Open project`. |
| Existing workspace is not Zephyr 4.1.0 | Select a matching workspace with `VITALITY_ZEPHYR_WORKSPACE`; see the advanced setup guide. |
| Nonempty incomplete workspace is reported | Inspect the path printed in the terminal before retrying. Setup does not delete an incomplete initial clone automatically. |
| Firmware compilation fails | Read the first build error in the startup terminal. The UI can stay open while you resolve it. |
| Linux/macOS preview does not appear | Check `build/portable-preview.log`, Tk availability and whether the session has a graphical display. |

After fixing an error, use **Tasks: Run Task > Vitality: Open project** again.
If Windows setup is blocked, the standalone preview command below can still run
without the firmware SDK.

## Run the watch preview on Windows

Build and launch from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Preview.ps1 -Run
```

The preview uses Windows Forms and the .NET Framework compiler included with
64-bit Windows. No npm, Python or browser server is needed.
After the first successful preview build, you can also open `build/VitalityPreview.exe`.

Select a screen on the left; use the six theme buttons at the bottom.
Swipe horizontally over the watch or use Left/Right keys. Home returns to the face.
Click the crown or press Space to sleep/wake. Heart Rate runs a timed **demo**
measurement; Activity toggles a demo workout. Turn simulated sensors off to see
unavailable values. The computer clock is enabled by default; switching it off uses a running demo clock.

The preview animates at a target of 30 frames per second: moving ring highlights,
pulsing hearts, scrolling demo traces, measurement spinners, sweeping analog hands,
swaying Nature leaves, twinkling Recovery stars and smooth screen/theme fades.
Animation pauses while sleeping or minimized. No animation packages are required.
The build script reuses an unchanged preview or closes it when replacing the executable.

The desktop preview is a separate design tool, **not a hardware or LVGL emulator**.
Its detailed visual rendering is ahead of the simpler firmware LVGL milestone.

## Run the portable preview on Linux/macOS

After setup, run from the project root:

```sh
bash tools/run-dev.sh preview
```

For preview only, an existing Python 3.10+ installation with Tk is sufficient:

```sh
python3 tools/dev.py preview
```

This native Tk preview reads the supplied themes and animates without pip packages.
See [VS Code setup](docs/VSCODE.md) for OS prerequisites.

## Build and check assets

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Assets.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Preview.ps1 -Render
```

Output: qspi_image/output/vitality_assets.bin and manifest.json.
The asset pack contains curated SVG-derived icons/logo and the supplied theme JSON.
SVG files remain the masters. Original assets remain untouched.
Rendering also runs preview checks and writes screenshots under build/screenshots.

## Firmware

The reproducible baseline is **Zephyr v4.1.0 / its pinned LVGL module**, using C,
CMake and west. This is an upstream Zephyr baseline; an nRF Connect SDK migration
must pin an NCS release and revalidate configuration/API compatibility.

After first-time setup, compile without launching the UI:

```powershell
# Windows
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Firmware.ps1
```

```sh
# Linux/macOS
bash tools/run-dev.sh firmware
```

Output: `build/firmware/zephyr/zephyr.elf` (and `zephyr.hex` when generated).
To disable simulated sensors, use `-ExtraConfig config/no_simulator.conf` with
the Windows script, or run the managed Python launcher on Linux/macOS:

```sh
.tools/venv/bin/python tools/dev.py firmware --extra-conf config/no_simulator.conf
```

The default application is a **headless development-kit target**, logging explicit
simulated data. A watch UI build requires the real display device tree/driver:
merge config/ui.conf only after integrating your panel. Merge config/qspi.conf
after defining and provisioning vitality_assets_partition on external flash.

There is no guessed custom PCB pin map. Display controller, pin assignments and
PMIC details are still required; see boards/vitality/README.md.
Do not flash the proposed 32 MiB partition map onto the DK's onboard flash.

## Portable C tests

On a machine with CMake and a C compiler:

```sh
cmake -S . -B build/core -DVITALITY_HOST_TESTS=ON
cmake --build build/core
ctest --test-dir build/core --output-on-failure
```

On Windows with gcc/clang/TinyCC:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-Core.ps1 -Compiler path/to/compiler.exe
```

The latter also tests the actual generated pack using the firmware asset reader.
CI definitions cover portable C and Windows preview/assets; they are not a substitute
for a Zephyr target build and bench tests.

## Project map

- src/app, include: state, events, normalized measurements.
- src/sensors, src/vitality: explicit demo data and demo-only scores.
- src/ui: optional LVGL screen implementation.
- src/assets, src/storage: validated asset reads, Q: bridge, Zephyr flash adapter.
- preview: interactive native desktop watch.
- assets/masters: cleaned SVG artwork used by preview and firmware packer.
- vitality_watch_assets: supplied assets, preserved.
- config, boards, qspi_image: feature overlays and hardware integration contract.
- docs: hardware, architecture, asset quality review and verification status.
- tests, tools: core tests, asset conversion and preview build.

Start with [PROJECT_SPEC.md](PROJECT_SPEC.md), [hardware](docs/HARDWARE.md),
[architecture/status](docs/ARCHITECTURE.md), and [verification](docs/VERIFICATION.md).
