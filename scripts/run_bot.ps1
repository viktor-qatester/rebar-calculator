# Запуск Telegram-бота (из корня проекта)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Прокси VPN (socks4) мешает боту — для запуска отключаем
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Сначала создайте venv: python -m venv .venv"
    exit 1
}

.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
.\.venv\Scripts\python.exe run_bot.py
