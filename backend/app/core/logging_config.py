import logging
import sys

from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """여러 요청이 동시에 들어와도 로그로 각 요청 흐름을 구별할 수 있도록,
    현재 실행 중인 요청의 request_id를 모든 로그 레코드에 자동으로 붙여준다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """ECS Fargate는 컨테이너가 재시작되면 로컬 디스크가 사라지므로 파일이 아닌
    stdout으로 출력하고, ECS의 awslogs 드라이버가 CloudWatch Logs로 수집하게 한다."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s"
    ))
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False
