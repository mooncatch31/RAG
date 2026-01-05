import logging, time, uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True

class AccessLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.logger = logging.getLogger("app.access")

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_var.set(rid)
        start = time.perf_counter()
        response = await call_next(request)
        if self.enabled:
            dur_ms = (time.perf_counter() - start) * 1000
            self.logger.info("%s %s -> %s %.1fms",
                             request.method, request.url.path, response.status_code, dur_ms)
        response.headers["x-request-id"] = rid
        request_id_var.reset(token)
        return response
