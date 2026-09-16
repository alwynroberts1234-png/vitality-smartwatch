param(
    [switch]$Plan,
    [ValidateSet('All','Detect','Check','Download','Launch')]
    [string]$Stage = 'All'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'

if ($Plan) {
    Write-Output 'UI only: detect Windows, check the existing .NET Framework compiler, then show the watch.'
    Write-Output 'No packages, Python, firmware SDK or toolchain will be downloaded.'
    exit 0
}
try {
    if ($Stage -in @('All','Detect')) {
        Write-Output ('[1/4] OS detected: Windows (' + [Environment]::OSVersion.VersionString + ')')
        if ($Stage -eq 'Detect') { exit 0 }
    }
    if ($Stage -in @('All','Check')) {
        Write-Output '[2/4] Check UI environment'
        if (Test-Path -LiteralPath $csc) { Write-Output 'Windows .NET Framework compiler found. No downloads needed.' }
        else { Write-Output 'Required Windows .NET Framework compiler is missing.' }
        if ($Stage -eq 'Check') { exit 0 }
    }
    if ($Stage -in @('All','Download')) {
        Write-Output '[3/4] Prepare UI environment'
        if (-not (Test-Path -LiteralPath $csc)) {
            throw 'The Windows .NET Framework compiler is missing. Restore/install .NET Framework before running the preview.'
        }
        Write-Output 'Using existing Windows components. Download size: 0 bytes.'
        if ($Stage -eq 'Download') { exit 0 }
    }
    Write-Output '[4/4] Build desktop preview if needed and show watch design'
    & (Join-Path $root 'tools\Build-Preview.ps1') -Run
} catch {
    [Console]::Error.WriteLine('UI SETUP: ' + $_.Exception.Message)
    exit 1
}
