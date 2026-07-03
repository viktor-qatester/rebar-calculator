"""Точка входа Telegram-бота (локально, polling)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from bot.app_factory import create_application

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        os.environ.pop(key, None)

    try:
        app = create_application()
    except ValueError:
        logger.error("TELEGRAM_BOT_TOKEN не задан. Добавьте токен в файл .env")
        sys.exit(1)

    logger.info("Бот запущен (polling). Остановка: Ctrl+C")
    logger.warning("Если бот уже в облаке — не запускайте polling одновременно!")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
