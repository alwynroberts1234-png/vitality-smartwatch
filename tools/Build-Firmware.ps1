param(
    [string]$ZephyrWorkspace = $env:VITALITY_ZEPHYR_WORKSPACE,
    [string]$Python = $env:VITALITY_ZEPHYR_PYTHON,
    [string]$Board = 'nrf52840dk/nrf52840',
    [string]$ExtraConfig,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$parent = Split-Path $root -Parent
$stateFile = Join-Path $root '.tools\environment.json'
if (Test-Path -LiteralPath $stateFile) {
    $state = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json
    if ($state.root -eq $root) {
        if (-not $ZephyrWorkspace) { $ZephyrWorkspace = $state.workspace }
        if (-not $Python) { $Python = $state.python }
        $env:PATH = ($state.path_entries -join ';') + ';' + $env:PATH
        if (-not $env:ZEPHYR_SDK_INSTALL_DIR) { $env:ZEPHYR_SDK_INSTALL_DIR = $state.sdk }
        if (-not $env:ZEPHYR_TOOLCHAIN_VARIANT) { $env:ZEPHYR_TOOLCHAIN_VARIANT = 'zephyr' }
    }
}
if (-not $ZephyrWorkspace) { $ZephyrWorkspace = Join-Path $parent 'zephyr-workspace' }
if (-not $Python) {
    $candidate = Join-Path $parent 'zephyr-env\Scripts\python.exe'
    if (Test-Path -LiteralPath $candidate) { $Python = $candidate }
    elseif ($env:VIRTUAL_ENV -and (Test-Path -LiteralPath (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'))) {
        $Python = Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'
    }
}
try {
    if (-not $Python -or -not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Zephyr Python environment not found. Expected $parent\zephyr-env\Scripts\python.exe. Set VITALITY_ZEPHYR_PYTHON for another installation. See docs\VSCODE.md."
    }
    $zephyrBase = Join-Path $ZephyrWorkspace 'zephyr'
    if (-not (Test-Path -LiteralPath (Join-Path $ZephyrWorkspace '.west') -PathType Container) -or
        -not (Test-Path -LiteralPath (Join-Path $zephyrBase 'CMakeLists.txt') -PathType Leaf)) {
        throw "Zephyr workspace not found at $ZephyrWorkspace. Set VITALITY_ZEPHYR_WORKSPACE for another installation. See docs\VSCODE.md."
    }
    # Use the selected virtual environment without relying on terminal activation.
    $oldPath = $env:PATH
    $oldBase = $env:ZEPHYR_BASE
    $env:PATH = (Split-Path $Python -Parent) + ';' + $env:PATH
    $env:ZEPHYR_BASE = $zephyrBase
    Push-Location $ZephyrWorkspace
    try {
        & $Python -m west --version
        if ($LASTEXITCODE -ne 0) { throw 'west is unavailable in the selected Python environment.' }
        if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
            throw 'CMake is missing from PATH. Install the Zephyr Windows prerequisites and restart VS Code.'
        }
        if (-not (Get-Command ninja -ErrorAction SilentlyContinue)) {
            throw 'Ninja is missing from PATH. Install the Zephyr Windows prerequisites and restart VS Code.'
        }
        if ($CheckOnly) {
            Write-Output "Build tools found. Workspace: $ZephyrWorkspace. Target: $Board."
            Write-Output 'SDK/toolchain compatibility is checked by the actual CMake build.'
            return
        }
        $build = Join-Path $root 'build\firmware'
        $westArgs = @('-m', 'west', 'build', '-p', 'auto', '-b', $Board, $root, '-d', $build)
        # Force a fresh CMake configure to use this workspace and any changed overlay.
        $westArgs += @('--', '-DVITALITY_HOST_TESTS=OFF')
        if ($ExtraConfig) {
            $configPath = if ([IO.Path]::IsPathRooted($ExtraConfig)) { $ExtraConfig } else { Join-Path $root $ExtraConfig }
            if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) { throw "Config not found: $configPath" }
            $westArgs += "-DEXTRA_CONF_FILE=$configPath"
        } else { $westArgs += '-DEXTRA_CONF_FILE=' }
        Write-Output "Compiling Vitality firmware for $Board ..."
        & $Python @westArgs
        if ($LASTEXITCODE -ne 0) { throw "Firmware compilation failed (west exit $LASTEXITCODE). See the build output above." }
        $elf = Join-Path $build 'zephyr\zephyr.elf'
        if (-not (Test-Path -LiteralPath $elf)) { throw "Build returned without firmware output: $elf" }
        Write-Output "Firmware built: $elf"
        $hex = Join-Path $build 'zephyr\zephyr.hex'
        if (Test-Path -LiteralPath $hex) { Write-Output "Flash image: $hex" }
    } finally {
        Pop-Location
        $env:PATH = $oldPath
        $env:ZEPHYR_BASE = $oldBase
    }
} catch {
    [Console]::Error.WriteLine("FIRMWARE BUILD: " + $_.Exception.Message)
    exit 1
}
