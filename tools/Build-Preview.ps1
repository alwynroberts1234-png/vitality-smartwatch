param([switch]$Run,[switch]$Render)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'build'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $out 'VitalityPreview.exe'
$sources=@((Join-Path $root 'preview\WatchPreview.cs'), (Join-Path $root 'tools\VectorAssets.cs'), $PSCommandPath)
$needsBuild=-not (Test-Path -LiteralPath $exe)
if (-not $needsBuild) {
    $built=(Get-Item -LiteralPath $exe).LastWriteTimeUtc
    $needsBuild=@($sources | Where-Object {(Get-Item -LiteralPath $_).LastWriteTimeUtc -gt $built}).Count -gt 0
}
if ($needsBuild) {
    # Compile before touching the working preview, so a compilation error leaves it available.
    $staged=Join-Path $out 'VitalityPreview.next.exe'
    & $csc /nologo /target:winexe /optimize+ /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll "/out:$staged" $sources[0] $sources[1]
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
