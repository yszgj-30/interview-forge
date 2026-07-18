$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
    & ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
}

& ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-audio.txt
Write-Host "本地语音依赖安装完成。首次转写时将下载 Whisper 模型。"
