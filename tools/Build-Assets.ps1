param()
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'qspi_image\output'
New-Item -ItemType Directory -Force -Path $out | Out-Null
# Rasterize the curated SVG masters; supplied originals remain untouched.
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$exe=Join-Path $out 'AssetPacker.exe'
& $csc /nologo /target:exe /optimize+ /r:System.Drawing.dll /r:System.Web.Extensions.dll "/out:$exe" (Join-Path $root 'tools\AssetPacker.cs') (Join-Path $root 'tools\VectorAssets.cs')
if($LASTEXITCODE -ne 0){throw 'Asset packer compilation failed'}
& $exe $root
if($LASTEXITCODE -ne 0){throw 'Asset pack generation failed'}
