param([string]$Compiler)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(-not $Compiler){$Compiler=Join-Path $root '.tools\tcc\tcc.exe'}
if(-not(Test-Path $Compiler)){throw 'Pass -Compiler pointing to gcc, clang or tcc; or use CMake host tests.'}
New-Item -ItemType Directory -Force -Path (Join-Path $root 'build') | Out-Null
Push-Location $root
try {
    & $Compiler -Wall -Werror -Iinclude tests/core_tests.c src/app/state.c src/assets/asset_manager.c src/sensors/simulator.c src/vitality/engine.c -o build/core_tests.exe
    if($LASTEXITCODE -ne 0){throw 'Core compilation failed'}
    & .\build\core_tests.exe qspi_image/output/vitality_assets.bin
    if($LASTEXITCODE -ne 0){throw 'Core tests failed'}
} finally {Pop-Location}
