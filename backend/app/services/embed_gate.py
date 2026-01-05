import threading
from contextlib import contextmanager
from app.config import settings

_sem = threading.BoundedSemaphore(value=max(1, int(settings.EMBED_MAX_CONCURRENCY)))

@contextmanager
def embed_gate():
    _sem.acquire()
    try:
        yield
    finally:
        _sem.release()
