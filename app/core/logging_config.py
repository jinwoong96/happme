import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """ECS Fargate는 컨테이너가 재시작되면 로컬 디스크가 사라지므로 파일이 아닌
    stdout으로 출력하고, ECS의 awslogs 드라이버가 CloudWatch Logs로 수집하게 한다."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False
