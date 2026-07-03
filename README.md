# Калькулятор арматуры 3.0

Упрощённый калькулятор **продольной арматуры** ленточного фундамента на Python + Streamlit.

## Что считает

- Количество поясов по высоте (авто или вручную)
- Количество продольных прутков на пояс (авто по ширине или вручную)
- Общий метраж с учётом нахлёстов (40 × диаметр)
- Сколько торговых прутков купить (+10% запас)

## Запуск

```powershell
cd "C:\Users\user\Projects\Калькулятор арматуры"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Или одной командой (если pip падает с SOCKS-ошибкой — см. ниже):

```powershell
.\scripts\install_deps.ps1
```

Откроется браузер на `http://localhost:8501`.

## Если pip: Missing dependencies for SOCKS support

**Причина:** на Windows или в VPN/Cursor настроен SOCKS-прокси. pip пытается идти через него, но для этого нужен пакет PySocks — которого ещё нет (замкнутый круг).

**Решение (автоматически):**

```powershell
.\scripts\install_deps.ps1
```

**Решение (вручную, 3 шага):**

```powershell
cd "C:\Users\user\Projects\Калькулятор арматуры"
mkdir wheels -Force
Invoke-WebRequest -Uri "https://files.pythonhosted.org/packages/8d/59/b4572118e098ac8e46e399a1dd0f2d85403ce8bbaad9ec79373ed6badaf9/PySocks-1.7.1-py3-none-any.whl" -OutFile "wheels\PySocks-1.7.1-py3-none-any.whl"
.\.venv\Scripts\python.exe -m pip install wheels\PySocks-1.7.1-py3-none-any.whl
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Если SOCKS-прокси вам не нужен — можно отключить его в настройках VPN или Windows (Параметры → Сеть → Прокси).

## Доступ с телефона

1. ПК и телефон в одной Wi‑Fi сети.
2. Узнай IP компьютера: `ipconfig` → IPv4-адрес.
3. На телефоне открой `http://<IP_ПК>:8501`.

## Тесты

```powershell
pytest tests/
```

Эталонный пример (H=60, B=40, L=74 м, d=10 мм, пруток 6 м):

- 315,2 м без запаса
- 346,72 м с запасом 10%
- 58 прутков по 6 м

## Disclaimer

Калькулятор упрощённый и **не заменяет** проект конструктора. Перед закупкой сверяйтесь с проектом или прорабом.

## Telegram-бот (@viktor_context_bot)

Бот с теми же расчётами + приём файлов проекта (без ИИ — показывает, что прочитал).

### Запуск на ПК

1. Токен в файле `.env` (строка `TELEGRAM_BOT_TOKEN=...`).
2. Установите зависимости (если ещё не ставили):

```powershell
cd "C:\Users\user\Projects\Калькулятор арматуры"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Запуск:

```powershell
python run_bot.py
```

Или: `.\scripts\run_bot.ps1`

4. В Telegram откройте бота → `/start`.

Пока бот работает **только когда запущен скрипт на ПК** (окно PowerShell не закрывать). Для работы 24/7 без ПК — позже настроим бесплатный хостинг (Render).

### Команды бота

- Кнопки: Ленточный, Плита, Сваи, Загрузить проект
- `/start` — меню
- `/cancel` — отмена ввода
- `/help` — подсказка

### Ошибка `Unknown scheme for proxy URL socks4://...`

На ПК включён VPN/прокси. Перед запуском выполните в том же терминале:

```powershell
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
$env:ALL_PROXY=""
python run_bot.py
```

Или используйте `.\scripts\run_bot.ps1` — прокси там уже сбрасывается.
