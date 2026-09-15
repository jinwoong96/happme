import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

from app.core.settings import settings
from app.core.request_context import get_request_id

_logger = logging.getLogger("bene_ai.step")
_logger.propagate = False
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    formatter = logging.Formatter("%(message)s")

    os.makedirs(settings.log_dir, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        os.path.join(settings.log_dir, "steps.jsonl"),
        when="midnight",
        backupCount=0,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    _logger.handlers = [file_handler, stream_handler]


@contextmanager
def log_step(pipeline: str, step: str, **context):
    """파이프라인(예: image_analyze) 안의 한 단계(예: detection)를 감싸서
    시작/종료/실행시간/성공여부를 JSON 한 줄로 남긴다. 성능 병목 확인(elapsed_ms)과
    사용 패턴 분석(어떤 파이프라인이 얼마나, 어떤 결과로 호출됐는지) 둘 다에 쓸 수 있게
    구조화된 필드로 남기고, steps.jsonl(파일) + stdout에 동시에 쓴다."""
    start = time.perf_counter()
    status = "ok"
    error = None
    try:
        yield
    except Exception as e:
        status = "error"
        error = f"{type(e).__name__}: {e}"
        raise
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "request_id": get_request_id(),
            "event": "step",
            "pipeline": pipeline,
            "step": step,
            "status": status,
            "elapsed_ms": elapsed_ms,
            **context,
        }
        if error:
            record["error"] = error
        _logger.info(json.dumps(record, ensure_ascii=False, default=str))


def log_event(pipeline: str, event: str, **context) -> None:
    """실행시간이 없는 단발성 이벤트(예: 파이프라인이 어느 단계에서 어떤 사유로 끝났는지)를
    남긴다. log_step과 같은 파일/포맷을 써서 나중에 같이 집계할 수 있게 한다."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": get_request_id(),
        "event": event,
        "pipeline": pipeline,
        **context,
    }
    _logger.info(json.dumps(record, ensure_ascii=False, default=str))
