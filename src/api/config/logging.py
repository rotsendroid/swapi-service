import logging
import logging.config

from api.config.settings import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()

    # Determine log level based on environment
    if settings.environment == "production":
        log_level = "INFO"
    elif settings.environment == "development":
        log_level = "DEBUG"
    else:  # testing
        log_level = "WARNING"

    # Disable SQLAlchemy's default logging first
    logging.getLogger("sqlalchemy.engine").handlers.clear()
    logging.getLogger("sqlalchemy.pool").handlers.clear()

    # Configure unified logging format
    logging_config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "unified": {
                "format": "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "unified",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            # Application loggers
            "api": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # FastAPI and uvicorn loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO" if settings.environment == "production" else "DEBUG",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy loggers with unified format
            "sqlalchemy.engine": {
                "level": "INFO" if settings.environment == "development" else "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(logging_config)

    # Force SQLAlchemy to use our unified format by clearing and reconfiguring
    for logger_name in ["sqlalchemy.engine", "sqlalchemy.pool"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel("INFO" if settings.environment == "development" else "WARNING")


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)
