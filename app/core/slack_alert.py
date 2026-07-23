import traceback

import httpx
from fastapi import Request

from app.core.settings import settings
from app.core.request_context import get_request_id

SERVICE_NAME = "bene_ai"


async def send_slack_alert(request: Request, exc: Exception) -> None:
    """요청 처리 중 발생한 예외를 슬랙 웹훅으로 전송한다. 웹훅 주소가 설정 안 돼 있으면
    아무것도 하지 않고, 전송 자체가 실패해도(네트워크 오류 등) 예외를 다시 던지지 않는다
    (알림 실패가 원래 요청 처리에 영향을 주면 안 되므로)."""
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
