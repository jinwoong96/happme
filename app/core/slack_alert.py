import traceback

import httpx
from fastapi import Request

from app.core.settings import settings

SERVICE_NAME = "bene_ai"


async def send_slack_alert(request: Request, exc: Exception) -> None:
    if not settings.slack_webhook_url:
        return

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(tb) > 3000:
        tb = tb[-3000:]

    environment = settings.sentry_environment or settings.app_env
    text = (
        f":rotating_light: *[{SERVICE_NAME}/{environment}] {type(exc).__name__}: {exc}*\n"
        f"`{request.method} {request.url.path}`\n"
        f"```{tb}```"
    )

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(settings.slack_webhook_url, json={"text": text})
    except Exception:
        pass
