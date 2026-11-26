# Builds SpotiParty for Windows on a Windows PC, without GitHub Actions:
#   desktop\dist\SpotiParty.exe  and  desktop\dist\SpotiParty-Setup-<version>.exe
#
#   powershell -ExecutionPolicy Bypass -File desktop\build-windows.ps1 -Version 2.4.0
#
# Needs Python 3.10+ (64-bit, from python.org or `winget install Python.Python.3.12`) and, for the installer,
# Inno Setup 6 (`winget install JRSoftware.InnoSetup`). It makes its own virtual environment in desktop\build\,
# so nothing is installed system-wide, and it starts the .exe once to check the page and the Hub answer.
param(
  [string]$Version = "",
  [string]$Python = ""
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Out = Join-Path $Root "desktop\dist"
$Work = Join-Path $Root "desktop\build"
Set-Location $Root

# A 64-bit Python 3.10+ with Tk.
if (-not $Python) {
  foreach ($c in @("py -3.13", "py -3.12", "py -3.11", "python")) {
    $exe, $arg = $c.Split(" ", 2)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $ok = & $exe $arg -c "import sys, struct, tkinter; sys.exit(not (sys.version_info >= (3, 10) and struct.calcsize('P') == 8))" 2>$null
    if ($LASTEXITCODE -eq 0) { $Python = (& $exe $arg -c "import sys; print(sys.executable)").Trim(); break }
  }
}
if (-not $Python) { throw "Geen 64-bit Python 3.10+ met Tk gevonden. Installeer: winget install Python.Python.3.12" }
Write-Host "-> Python: $Python"

Write-Host "-> Bouwomgeving in desktop\build\venv"
$Venv = Join-Path $Work "venv"
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) { & $Python -m venv $Venv; if ($LASTEXITCODE) { throw "venv failed" } }
& (Join-Path $Venv "Scripts\python.exe") -m pip install --quiet --disable-pip-version-check --upgrade pyinstaller pillow certifi pystray
if ($LASTEXITCODE) { throw "pip install failed" }

if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Geef een versie mee, zoals -Version 2.7.0: de auto-updater vergelijkt ermee." }
# The version inside the .exe, for the auto-updater (it compares it with the newest GitHub release).
[IO.File]::WriteAllText((Join-Path $Root "desktop\sp_version.py"),
  "# The version of this build. desktop/build-windows.ps1 -Version writes it; the auto-updater compares with it.`nVERSION = `"$Version`"`n")

Write-Host "-> SpotiParty.exe"
# Absolute paths: PyInstaller resolves --icon and --add-data relative to the spec folder.
& (Join-Path $Venv "Scripts\pyinstaller.exe") --noconfirm --clean --onefile --windowed --name SpotiParty `
  --icon "$Root\desktop\icon.ico" --add-data "$Root\web;web" --add-data "$Root\hub;hub" --add-data "$Root\brand\app;brand\app" --paths "$Root\hub" --hidden-import sp_party --hidden-import pystray._win32 `
  --distpath $Out --workpath "$Work\work" --specpath "$Work\spec" "$Root\desktop\spotiparty_app.py"
if ($LASTEXITCODE) { throw "PyInstaller failed" }

Write-Host "-> Rooktest"
# A SpotiParty that still runs would answer instead (a second start only opens a window): stop it first.
Get-Process -Name SpotiParty -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 1
if (Get-NetTCPConnection -State Listen -LocalPort 8769, 8770 -ErrorAction SilentlyContinue) {
  Write-Warning "Poort 8769 of 8770 is al in gebruik: de rooktest test dan niet deze build."
}
# -TimeoutSec: a request that hangs counts as a miss, so the test can never wait forever.
$p = Start-Process (Join-Path $Out "SpotiParty.exe") -PassThru
$ok = $false; $hubOk = $false
foreach ($i in 1..30) {
  try { if ((Invoke-WebRequest http://127.0.0.1:8769/index.html -UseBasicParsing -TimeoutSec 3).Content -match "SpotiParty") { $ok = $true; break } } catch {}
  Start-Sleep 1
}
foreach ($i in 1..10) {
  try { if ((Invoke-WebRequest http://127.0.0.1:8770/api/ping -UseBasicParsing -TimeoutSec 3).Content -match "hub") { $hubOk = $true; break } } catch {}
  Start-Sleep 1
}
# --onefile runs as two processes (a launcher and the app): stop both, or the next run finds this one.
Get-Process -Name SpotiParty -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
if (-not $ok) { throw "SpotiParty.exe gaf de pagina niet (127.0.0.1:8769)" }
if (-not $hubOk) { Write-Warning "De Hub antwoordde niet op :8770 (draait er al een Hub op dit netwerk? Dan wordt deze pc een scherm)." }

$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
  Write-Warning "Inno Setup 6 niet gevonden: alleen SpotiParty.exe gemaakt. Installeer: winget install JRSoftware.InnoSetup"
} else {
  Write-Host "-> SpotiParty-Setup-$Version.exe"
  & $iscc /Q "/DAppVersion=$Version" (Join-Path $Root "desktop\installer.iss")
  if ($LASTEXITCODE) { throw "ISCC failed" }
}

Write-Host ""
Write-Host "Klaar:"
Get-ChildItem $Out -Filter "SpotiParty*.exe" | ForEach-Object { Write-Host ("   {0} ({1:N1} MB)" -f $_.FullName, ($_.Length / 1MB)) }
