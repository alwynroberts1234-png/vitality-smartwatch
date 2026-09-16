param([switch]$Run,[switch]$Render)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'build'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $out 'VitalityPreview.exe'
$iconDirectory=Join-Path $root 'assets\app'
$icon=Join-Path $iconDirectory 'vitality.ico'
$iconPng=Join-Path $iconDirectory 'vitality.png'
$iconSources=@((Join-Path $root 'assets\masters\vitality_mark.svg'), (Join-Path $root 'tools\AppIcon.cs'), (Join-Path $root 'tools\VectorAssets.cs'))
$needsIcon=(-not (Test-Path -LiteralPath $icon)) -or (-not (Test-Path -LiteralPath $iconPng))
if (-not $needsIcon) {
    $iconBuilt=(Get-Item -LiteralPath $icon).LastWriteTimeUtc
    $needsIcon=@($iconSources | Where-Object {(Get-Item -LiteralPath $_).LastWriteTimeUtc -gt $iconBuilt}).Count -gt 0
}
if ($needsIcon) {
    New-Item -ItemType Directory -Force -Path $iconDirectory | Out-Null
    $iconBuilder=Join-Path $out 'AppIcon.exe'
    & $csc /nologo /target:exe /r:System.Drawing.dll "/out:$iconBuilder" $iconSources[1] $iconSources[2]
    if ($LASTEXITCODE -ne 0) { throw 'App icon builder compilation failed' }
    & $iconBuilder $iconSources[0] $icon $iconPng
    if ($LASTEXITCODE -ne 0) { throw 'App icon generation failed' }
}
$sources=@((Join-Path $root 'preview\WatchPreview.cs'), (Join-Path $root 'tools\VectorAssets.cs'), (Join-Path $root 'preview\Rewards.cs'), $PSCommandPath)
$needsBuild=-not (Test-Path -LiteralPath $exe)
if (-not $needsBuild) {
    $built=(Get-Item -LiteralPath $exe).LastWriteTimeUtc
    $needsBuild=@(($sources + @($icon)) | Where-Object {(Get-Item -LiteralPath $_).LastWriteTimeUtc -gt $built}).Count -gt 0
}
if ($needsBuild) {
    # Compile before touching the working preview, so a compilation error leaves it available.
    $staged=Join-Path $out 'VitalityPreview.next.exe'
    & $csc /nologo /target:winexe /optimize+ /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll "/win32icon:$icon" "/out:$staged" $sources[0] $sources[1] $sources[2]
    if($LASTEXITCODE -ne 0){throw 'Preview compilation failed'}
    $running=@(Get-Process VitalityPreview -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe})
    foreach($process in $running) {
        if (-not $process.CloseMainWindow() -or -not $process.WaitForExit(5000)) {
            throw 'Close the running Vitality preview, then run the task again.'
        }
    }
    Move-Item -LiteralPath $staged -Destination $exe -Force
}
if($Render) {
    $check=Start-Process -FilePath $exe -ArgumentList '--render' -WorkingDirectory $root -WindowStyle Hidden -PassThru -Wait
    if($check.ExitCode -ne 0){throw 'Preview render failed; see build\preview-error.txt'}
}
if($Run) {
    $running=@(Get-Process VitalityPreview -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $exe})
    if($running.Count -eq 0) {
        Start-Process -FilePath $exe -WorkingDirectory $root -WindowStyle Normal
    } else { Write-Output 'Vitality preview is already running.' }
}
Write-Output "Preview: $exe"
