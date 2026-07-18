$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
$env:INTERVIEW_FORGE_DB = Join-Path $root "data\demo.db"
$env:INTERVIEW_FORGE_AUTO_DEMO = "1"
& ".venv\Scripts\python.exe" -m streamlit run app.py
