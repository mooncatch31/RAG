import logging
from fastapi import FastAPI, APIRouter
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_config import setup_console_logging
from app.request_logging import AccessLogMiddleware
from app.db.models import Base
from app.db.session import engine
from app.routers import health, upload, ask, documents, feedback

def create_app() -> FastAPI:
    setup_console_logging(level=settings.LOG_LEVEL)

    app = FastAPI(
        title=settings.APP_NAME,
        default_response_class=ORJSONResponse,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    # Create tables (dev convenience; for prod use Alembic)
    Base.metadata.create_all(bind=engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS_LIST,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"] if settings.CORS_ALLOW_METHODS == "*" else [settings.CORS_ALLOW_METHODS],
        allow_headers=["*"] if settings.CORS_ALLOW_HEADERS == "*" else [settings.CORS_ALLOW_HEADERS],
    )

    app.add_middleware(AccessLogMiddleware, enabled=settings.LOG_ACCESS)

    api = APIRouter(prefix="/api")

    @api.get("/", tags=["root"])
    def api_root():
        return {"status": "ok", "name": settings.APP_NAME}

    api.include_router(health.router, tags=["health"])
    api.include_router(upload.router, tags=["upload"])
    api.include_router(ask.router, tags=["ask"])
    api.include_router(documents.router, tags=["documents"])
    api.include_router(feedback.router, tags=["feedback"])

    app.include_router(api)
    logging.getLogger("app").info("Backend started: %s", settings.APP_NAME)
    return app

app = create_app()
