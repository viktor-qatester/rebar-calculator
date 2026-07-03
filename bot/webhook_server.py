"""HTTP-сервер для деплоя на Render (webhook + /health)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from telegram import Update

from bot.app_factory import create_application

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_env() -> None:
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


load_env()
ptb_app = create_application()


async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def telegram_webhook(request: Request) -> Response:
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response()


async def on_startup() -> None:
    await ptb_app.initialize()
    await ptb_app.start()

    webhook_base = (
        os.getenv("WEBHOOK_URL", "").strip()
        or os.getenv("RENDER_EXTERNAL_URL", "").strip()
    ).rstrip("/")
    if not webhook_base:
        logger.error(
            "Не задан WEBHOOK_URL и нет RENDER_EXTERNAL_URL. "
            "На Render URL подставится сам; локально укажите WEBHOOK_URL."
        )
        return

    webhook_url = f"{webhook_base}/webhook"
    await ptb_app.bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message"],
        drop_pending_updates=True,
    )
    logger.info("Webhook установлен: %s", webhook_url)


async def on_shutdown() -> None:
    await ptb_app.stop()
    await ptb_app.shutdown()


app = Starlette(
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)
app.add_route("/", health, methods=["GET"])
app.add_route("/health", health, methods=["GET"])
app.add_route("/webhook", telegram_webhook, methods=["POST"])
