from fastapi import Header
from app.config import settings

def workspace_header(x_workspace: str | None = Header(default=None)) -> str:
    return x_workspace or settings.WORKSPACE_DEFAULT

def openai_key_header(x_openai_key: str | None = Header(default=None)) -> str | None:
    return x_openai_key or settings.OPENAI_API_KEY
