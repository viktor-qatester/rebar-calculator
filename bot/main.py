"""Точка входа Telegram-бота."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import Application
from telegram.request import HTTPXRequest

from bot.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан. Добавьте токен в файл .env")
        sys.exit(1)

    http_kwargs = {"trust_env": False}
    app = (
        Application.builder()
        .token(token)
        .request(HTTPXRequest(proxy=None, httpx_kwargs=http_kwargs))
        .get_updates_request(HTTPXRequest(proxy=None, httpx_kwargs=http_kwargs))
        .build()
    )
    register_handlers(app)

    logger.info("Бот запущен. Остановка: Ctrl+C")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
