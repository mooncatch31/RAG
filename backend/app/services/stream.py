from typing import Iterable
from fastapi.responses import StreamingResponse

def text_stream(generator: Iterable[str]):
    return StreamingResponse(generator, media_type="text/plain; charset=utf-8")
