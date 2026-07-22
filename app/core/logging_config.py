import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """여러 요청이 동시에 들어와도 로그로 각 요청 흐름을 구별할 수 있도록,
    현재 실행 중인 요청의 request_id를 모든 로그 레코드에 자동으로 붙여준다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def setup_logging(log_dir: str, level: int = logging.INFO) -> None:
    """EC2는 디스크가 영구적이므로 로테이팅 파일 + stdout 둘 다에 남긴다.
    자정마다 날짜별로 파일을 나눠서(ai.log.YYYY-MM-DD) upload_logs_to_s3.py가 전날 이전
    파일만 골라 S3에 올리고 지울 수 있게 한다. backupCount=0이라 핸들러 자신은 옛 파일을
    지우지 않고, 삭제는 업로드 스크립트가 S3 업로드 확인 후에만 한다."""
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s"
    )

    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "ai.log"),
        when="midnight",
        backupCount=0,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [file_handler, stream_handler]

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [file_handler, stream_handler]
        uvicorn_logger.propagate = False
