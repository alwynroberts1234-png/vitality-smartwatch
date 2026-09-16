# VS Code startup

Open the repository folder in local desktop VS Code. `.vscode/tasks.json` runs
`Vitality: Open project` on `folderOpen`. It delegates setup to scripts because
JSON alone cannot detect and install a development environment.

The task uses `dependsOrder: "sequence"` to run four visible stages:

1. **Vitality: 1. Detect OS** — identify Windows, Linux or macOS.
2. **Vitality: 2. Check environment** — report missing host tools and whether the
   saved development environment is ready. This stage installs nothing and allows
   missing dependencies to be handled by stage 3.
3. **Vitality: 3. Download environment** — install missing host tools, prepare
   `.tools/venv`, Zephyr **v4.1.0** and the ARM SDK, and save paths in
   `.tools/environment.json`. Reuse an already prepared environment.
4. **Vitality: 4. Compile and show design** — launch the animated preview, then
   compile the headless nRF52840 DK firmware, without downloading dependencies.

A stage failure prevents subsequent stages from starting. Run **Vitality: Open
project** for the complete sequence; individual stages are also available through
**Tasks: Run Task**.

Later opens validate and reuse the saved environment, launch or reuse the preview,
and build incrementally. Nothing flashes hardware. The preview is a separate
application; it does not execute the firmware.

## A computer without development tools

| OS | Host setup | UI |
|---|---|---|
| Windows | PowerShell; existing Chocolatey installs missing Python, Git, gperf, dtc, wget and 7zip | Windows Forms |
| macOS | Bash; existing Homebrew installs missing Python/Tk, Git, gperf, dtc and wget | Python/Tk |
| Linux | Bash; apt, dnf or pacman installs missing Python/Tk and host tools | Python/Tk |

The scripts do not install package managers. If Chocolatey or Homebrew is absent,
follow the terminal instruction to install it from its official site, or install
the host prerequisites yourself, then rerun `Vitality: Open project`.
Windows package installation may require an administrator terminal; Linux may
request your sudo password. A task cannot grant itself administrator privileges.

First setup needs internet access and several GB of disk space. Zephyr and its SDK
are substantial downloads, even though the UI adds no pip/npm framework.
Python packages and the new workspace/SDK are stored under the ignored `.tools`
directory. Host packages use their package manager's normal locations;
`west zephyr-export` and SDK setup also register their locations with CMake.

Setup errors stop startup and remain visible in its terminal. Correct the error
and use **Tasks: Run Task > Vitality: Open project** to retry. Interrupted module
downloads can resume. An incomplete initial clone without `.west` requires
inspection before retrying; the script does not delete it automatically.

After successful setup, a firmware compile error leaves the preview open. If setup
fails, Windows users can still run the independent **Vitality: Start preview** task.

## VS Code trust and automatic tasks

`runOn: folderOpen` remains supported. The folder must be trusted, and automatic
tasks must be allowed. This repository sets `task.allowAutomaticTasks` to `on`;
workspace trust and organization policies still apply.

Use **Workspaces: Manage Workspace Trust** to review trust. If prompted, use
**Tasks: Manage Automatic Tasks > Allow Automatic Tasks**. Then reopen the folder
or run **Developer: Reload Window**. You can also run the task manually.
Set `task.allowAutomaticTasks` to `off` to disable startup.

References: [VS Code task run behavior](https://code.visualstudio.com/docs/debugtest/tasks#_run-behavior),
[Workspace Trust](https://code.visualstudio.com/docs/editing/workspaces/workspace-trust).

## Inspect without installing

Windows:

```powershell
powershell -NoProfile -File tools/Setup-Environment.ps1 -Plan
```

Linux/macOS:

```sh
bash tools/setup-host.sh --plan
```

These commands print the plan without downloading or installing anything.

## Existing environments and manual commands

Setup reuses a sibling `../zephyr-workspace` if present, or the workspace selected
by `VITALITY_ZEPHYR_WORKSPACE`. It checks for Zephyr 4.1.0 before updating modules;
other versions are rejected. Otherwise it creates `.tools/zephyr-workspace`.
Setup always uses its own Python venv. Set `VITALITY_BOOTSTRAP_PYTHON` to an existing
Python executable for creating that venv.

Manual builds prefer saved paths. Explicit launcher arguments and
`VITALITY_ZEPHYR_WORKSPACE` / `VITALITY_ZEPHYR_PYTHON` override workspace/interpreter
selection. Without saved paths, the earlier sibling `zephyr-workspace` and
`zephyr-env` layout remains supported by the firmware launchers.

**Ctrl+Shift+B** builds firmware. **Tasks: Run Task** exposes startup, firmware and
preview. The expected output is `build/firmware/zephyr/zephyr.elf`.

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Firmware.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Build-Preview.ps1 -Run
```

Linux/macOS, after automatic setup:

```sh
bash tools/run-dev.sh firmware
bash tools/run-dev.sh preview
```

With a manually configured Python environment, `python3 tools/dev.py firmware`
and `python3 tools/dev.py preview` remain available. Tk must come from your Python
or OS distribution, not pip. Windows preview uses the .NET Framework compiler.

## Limits and verification

The firmware is a headless nRF52840 DK foundation. A custom watch still needs its
board definition, display driver and GPIO map. The SVG asset packer remains
Windows-only; default headless firmware and portable preview do not need it.
Remote/headless VS Code sessions need a graphical display to show the UI.

Bootstrap tests mock installation commands; they do not install tools. Local checks
cover launcher behavior, cached setup, failure handling, SDK selection, PowerShell
syntax and plan mode. Full first-time installation and the actual Zephyr build
have not been run. Linux/macOS native execution remains unverified in this session;
CI includes shell syntax checks and portable tests.

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

Host prerequisites follow the
[pinned Zephyr guide](https://github.com/zephyrproject-rtos/zephyr/blob/v4.1.0/doc/develop/getting_started/index.rst).
