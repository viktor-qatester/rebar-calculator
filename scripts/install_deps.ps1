# Установка зависимостей калькулятора арматуры.
# Решает проблему "Missing dependencies for SOCKS support":
# сначала ставим PySocks из локального wheel (без сети в pip), затем requirements.txt.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Pip = Join-Path $ProjectRoot ".venv\Scripts\pip.exe"
$WheelsDir = Join-Path $ProjectRoot "wheels"
$PySocksWheel = Join-Path $WheelsDir "PySocks-1.7.1-py3-none-any.whl"

Write-Host "Проект: $ProjectRoot"

if (-not (Test-Path $Python)) {
    Write-Host "Создаю виртуальное окружение..."
    python -m venv .venv
}

New-Item -ItemType Directory -Force -Path $WheelsDir | Out-Null

if (-not (Test-Path $PySocksWheel)) {
    Write-Host "Скачиваю PySocks wheel..."
    $json = Invoke-RestMethod "https://pypi.org/pypi/PySocks/json"
    $url = ($json.releases."1.7.1" | Where-Object { $_.filename -eq "PySocks-1.7.1-py3-none-any.whl" }).url
    Invoke-WebRequest -Uri $url -OutFile $PySocksWheel -UseBasicParsing
}

Write-Host "Устанавливаю PySocks локально..."
& $Python -m pip install $PySocksWheel

Write-Host "Устанавливаю зависимости из requirements.txt..."
& $Python -m pip install -r requirements.txt

Write-Host ""
Write-Host "Готово. Проверка:"
& $Python verify_calc.py
& $Python -m pytest tests/ -v

Write-Host ""
Write-Host "Запуск калькулятора:"
Write-Host "  .\.venv\Scripts\streamlit.exe run app.py"
