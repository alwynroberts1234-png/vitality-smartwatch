param(
    [switch]$Plan,
    [ValidateSet('All','Detect','Check','Download','Launch')]
    [string]$Stage = 'All'
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if($Plan) {
    Write-Output 'Plan: use existing Chocolatey for missing Python/Git/gperf/dtc/wget/7zip.'
    Write-Output 'Prepare .tools/venv, Zephyr v4.1.0 and the ARM SDK; launch preview and compile.'
    Write-Output 'No changes. Missing Chocolatey or administrator rights require one-time manual setup.'
    exit 0
}
if($Stage -eq 'Detect') {
    Write-Output ('[1/4] OS detected: Windows (' + [Environment]::OSVersion.VersionString + ')')
    exit 0
}
if($Stage -eq 'Launch') {
    Write-Output '[4/4] Compile firmware and show design'
    $managedPython = Join-Path $root '.tools\venv\Scripts\python.exe'
    if(-not (Test-Path -LiteralPath $managedPython)) {
        [Console]::Error.WriteLine('Environment missing. Run Vitality: Open project first.')
        exit 1
    }
    & $managedPython (Join-Path $root 'tools\setup_env.py') --launch-only
    exit $LASTEXITCODE
}
function Find-Python {
    $candidates=@($env:VITALITY_BOOTSTRAP_PYTHON,
        (Join-Path $root '.tools\venv\Scripts\python.exe'),
        'C:\Python312\python.exe','C:\Python311\python.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'))
    foreach($name in @('python3','python')) {
        $command=Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
        if($command -and $command.Source -notlike '*\WindowsApps\*'){$candidates+=$command.Source}
    }
    foreach($candidate in $candidates) {
        if($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            try {
                & $candidate -c 'import sys, venv; assert sys.version_info >= (3,10)' 2>$null
                if($LASTEXITCODE -eq 0){return $candidate}
            } catch { continue }
        }
    }
    return $null
}
try {
    $env:PATH=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')+';'+$env:PATH
    $python=Find-Python
    $packages=@()
    if(-not $python){$packages+='python311'}
    $needed=@{git='git';gperf='gperf';dtc='dtc-msys2';wget='wget';'7z'='7zip'}
    foreach($tool in $needed.Keys) {
        if(-not(Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue)){$packages+=$needed[$tool]}
    }
    if($Stage -eq 'Check') {
        Write-Output '[2/4] Check development environment (no installation)'
        if($packages.Count) { Write-Output ('Missing host packages: ' + ($packages -join ', ')) }
        else { Write-Output 'Host prerequisites found.' }
        if($packages.Count -and -not(Get-Command choco -ErrorAction SilentlyContinue)) {
            Write-Output 'Chocolatey is missing; the download stage will require host prerequisites to be installed manually.'
        }
        if($python) {
            & $python (Join-Path $root 'tools\setup_env.py') --check
            exit $LASTEXITCODE
        }
        Write-Output 'Python/environment missing; continuing to the download stage.'
        exit 0
    }
    Write-Output '[3/4] Download and prepare missing development tools'
    if($packages.Count -gt 0) {
        if(-not(Get-Command choco -ErrorAction SilentlyContinue)) {
            throw 'Chocolatey is missing. Install it from https://chocolatey.org/install or install the listed host prerequisites manually, then rerun.'
        }
        Write-Output ('Installing missing host packages: '+($packages -join ', '))
        foreach($package in $packages) {
            & choco install $package -y --no-progress
            if($LASTEXITCODE -notin @(0,3010)){throw "Package setup failed: $package. Administrator permission may be required."}
        }
        $env:PATH=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')+';'+$env:PATH
        $python=Find-Python
    }
    if(-not $python){throw 'Python is still unavailable. Set VITALITY_BOOTSTRAP_PYTHON to its executable.'}
    foreach($tool in $needed.Keys) {
        if(-not(Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue)){throw "Host tool still missing: $tool"}
    }
    $setupArgs = @((Join-Path $root 'tools\setup_env.py'))
    if($Stage -eq 'All') { $setupArgs += '--start' }
    & $python @setupArgs
    if($LASTEXITCODE -ne 0){throw "Environment setup/start failed (exit $LASTEXITCODE)."}
} catch {
    [Console]::Error.WriteLine('SETUP: '+$_.Exception.Message)
    exit 1
}
