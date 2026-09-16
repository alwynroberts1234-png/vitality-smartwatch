# VS Code UI startup

Opening a trusted repository folder runs `Vitality: Open project` in five stages:

1. **Detect OS**.
2. **Check UI environment**, without installing anything.
3. **Prepare UI environment**, reusing existing tools or installing missing Python/Tk packages.
4. **Show watch design**, using Windows Forms on Windows and Tk on Linux/macOS.
5. **Run bluetooth environment setup**, executing the user-configured remote script.

Step 4 builds the Windows desktop preview if needed and opens it. On Linux/macOS
it runs the Python preview. VS Code waits for the preview's ready message before
starting step 5; it does not wait for the watch window to close. On Windows the
launcher waits for the application's message loop before reporting readiness.

Step 5 executes code from the external endpoint in `tasks.json`. Its contents and
downloads are not verified by this project. The download information below applies
only to the local UI setup in steps 1-4, not to the external script.

Firmware setup and compilation are excluded. The firmware source and optional
manual build helpers remain. The previous SDK downloader has been removed.

## Downloads

| OS | Behavior |
|---|---|
| Windows | Use the existing .NET Framework compiler and Windows Forms. No downloads. Missing components produce an error with instructions. |
| Linux | Reuse Python 3.10+ with Tk. Otherwise install `python3-tk` (apt), `python3-tkinter` (dnf), or `python tk` (pacman), including their dependencies. |
| macOS | Reuse Python 3.10+ with Tk. Otherwise use existing Homebrew to install `python-tk@3.12` and its dependencies. |

No pip packages or virtual environments are needed. Download size depends on the
existing runtime and OS packages. Linux installation may request sudo. The project
does not install package managers.

Linux/macOS can select an existing runtime with `VITALITY_PREVIEW_PYTHON`. The
chosen executable is saved in `.tools/preview-python`. Previously installed
firmware development tools are left in place; they are not needed by this flow.

## Trust and automatic tasks

The repository sets `task.allowAutomaticTasks` to `on`. Tasks still require a
trusted workspace and must comply with organization policies.

If you clicked **Don't Allow**:

1. Open the Command Palette: Ctrl+Shift+P (Windows/Linux), Cmd+Shift+P (macOS).
2. Run **Tasks: Manage Automatic Tasks**, then **Allow Automatic Tasks**.
3. Run **Developer: Reload Window**.

For an untrusted folder, review **Workspaces: Manage Workspace Trust** first.
To run immediately, select **Tasks: Run Task > Vitality: Open project**.
To disable startup, set `task.allowAutomaticTasks` to `off`.

Reference: [VS Code automatic tasks](https://code.visualstudio.com/docs/debugtest/tasks#_control-automatic-task-execution).

## Manual commands

From the repository root:

```powershell
# Windows: prepare UI and launch
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1
# Inspect only
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Setup-Environment.ps1 -Plan
```

```sh
# Linux/macOS: prepare UI and launch
bash tools/setup-host.sh
# Inspect only
bash tools/setup-host.sh --plan
# Launch without package installation
bash tools/run-dev.sh preview
```

Individual stages use `-Stage Detect|Check|Download|Launch` on Windows and
`--detect|--check|--download|--launch` on Linux/macOS. The Download stage name is
retained in the script interface; it downloads nothing if the runtime is ready.

A failure stops the sequence. Fix the reported prerequisite and rerun
`Vitality: Open project`. Preview errors appear in the task terminal. On
Linux/macOS the preview task stays active until its window closes.

## Limits

The preview is a desktop design application, not a firmware emulator.
Remote/headless sessions need access to a graphical display. The Windows asset
packer is optional and is not part of startup.

Windows preview rendering and UI setup checks run locally. Native Linux/macOS
runtime installation remains unverified here; CI includes portable tests and Bash
syntax checks. Firmware cross-compilation remains unverified and is outside this
UI setup.
