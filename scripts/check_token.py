"""One-off check: .env token format + Telegram getMe. Do not commit."""
import json
import re
import urllib.request
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
token = None
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("TELEGRAM_BOT_TOKEN="):
        token = line.split("=", 1)[1].strip()
        break

if not token:
    raise SystemExit("FAIL: TELEGRAM_BOT_TOKEN пустой или строка не найдена")
if " " in token or '"' in token or "'" in token:
    raise SystemExit("FAIL: уберите пробелы и кавычки вокруг токена")
if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token):
    raise SystemExit("FAIL: формат токена не похож на Telegram")

req = urllib.request.Request(f"https://api.telegram.org/bot{token}/getMe")
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.load(resp)

if not data.get("ok"):
    raise SystemExit(f"FAIL: Telegram ответил ошибкой: {data}")

username = data["result"].get("username", "")
print("OK: формат файла правильный")
print(f"OK: токен рабочий, бот @{username}")
