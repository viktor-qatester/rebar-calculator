"""Запуск бота в облаке (Render): webhook + health-check."""

import os

from bot.webhook_server import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
