import logging, logging.config
from app.request_logging import RequestContextFilter

def setup_console_logging(level: str = "INFO"):
    fmt = "%(asctime)s %(levelname)s %(name)s [rid=%(request_id)s] %(message)s"
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": fmt}},
        "filters": {"request_ctx": {"()": RequestContextFilter}},
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default", "filters": ["request_ctx"]}
        },
        "loggers": {
            "app": {"handlers": ["console"], "level": level, "propagate": False},
            "app.access": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn": {"level": level},
            "uvicorn.error": {"level": level},
            "uvicorn.access": {"level": "WARNING"},
        },
        "root": {"handlers": ["console"], "level": level, "filters": ["request_ctx"]},
    })
