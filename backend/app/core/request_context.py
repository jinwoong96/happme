import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-Id"

# 요청마다 독립적인 값을 가져야 하므로(다른 요청과 섞이면 안 됨) 전역 변수 대신
# ContextVar를 사용한다. 값이 없으면 "-"로 표시한다.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    """요청 하나를 구별할 새 request_id를 만든다 (uuid 앞 16자리)."""
    return uuid.uuid4().hex[:16]


def set_request_id(value: str) -> None:
    """현재 요청의 request_id를 저장한다."""
    _request_id_var.set(value)


def get_request_id() -> str:
    """현재 요청의 request_id를 가져온다. 저장된 값이 없으면 "-"."""
    return _request_id_var.get()
