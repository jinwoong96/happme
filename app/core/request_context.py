import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-Id"

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def set_request_id(value: str) -> None:
    _request_id_var.set(value)


def get_request_id() -> str:
    return _request_id_var.get()
