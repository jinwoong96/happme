import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: str, level: int = logging.INFO) -> None:
    """EC2는 디스크가 영구적이므로 로테이팅 파일 + stdout 둘 다에 남긴다."""
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "ai.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [file_handler, stream_handler]

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [file_handler, stream_handler]
        uvicorn_logger.propagate = False
