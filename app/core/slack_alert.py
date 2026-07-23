import traceback

import httpx
from fastapi import Request

from app.core.settings import settings
from app.core.request_context import get_request_id

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
        f"`{request.method} {request.url.path}` · request_id=`{get_request_id()}`\n"
        f"```{tb}```"
    )

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(settings.slack_webhook_url, json={"text": text})
    except Exception:
        pass


async def send_slack_status_alert(request: Request, status_code: int) -> None:
    """예외 없이(예: 명시적으로 raise된 HTTPException) 5xx 응답이 나간 경우를 위한 알림.
    traceback이 없으므로 상태 코드와 경로만 남긴다."""
    if not settings.slack_webhook_url:
        return

    environment = settings.sentry_environment or settings.app_env
    text = (
        f":rotating_light: *[{SERVICE_NAME}/{environment}] HTTP {status_code}*\n"
        f"`{request.method} {request.url.path}` · request_id=`{get_request_id()}`"
    )

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(settings.slack_webhook_url, json={"text": text})
    except Exception:
        pass
