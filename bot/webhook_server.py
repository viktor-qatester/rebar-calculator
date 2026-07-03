"""HTTP-сервер для деплоя на Render (webhook + /health)."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ptb_app: Application | None = None


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


async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def telegram_webhook(request: Request) -> Response:
    if ptb_app is None:
        return Response(status_code=503)
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response()


@asynccontextmanager
async def lifespan(_: Starlette):
    global ptb_app

    from bot.app_factory import create_application

    try:
        ptb_app = create_application()
        await ptb_app.initialize()
        await ptb_app.start()
    except Exception:
        logger.exception("Не удалось запустить Telegram-приложение")
        raise

    webhook_base = (
        os.getenv("WEBHOOK_URL", "").strip()
        or os.getenv("RENDER_EXTERNAL_URL", "").strip()
    ).rstrip("/")
    if webhook_base:
        webhook_url = f"{webhook_base}/webhook"
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message"],
            drop_pending_updates=True,
        )
        logger.info("Webhook установлен: %s", webhook_url)
    else:
        logger.error("Нет WEBHOOK_URL и RENDER_EXTERNAL_URL")

    yield

    if ptb_app is not None:
        await ptb_app.stop()
        await ptb_app.shutdown()


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/", health, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/webhook", telegram_webhook, methods=["POST"]),
    ],
)
