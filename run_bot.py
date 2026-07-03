"""Запуск Telegram-бота: python run_bot.py"""

import os

# Прокси из VPN (socks4://…) ломает httpx у python-telegram-bot
for _key in (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
):
    os.environ.pop(_key, None)

from bot.main import main

if __name__ == "__main__":
    main()
