"""
    module to add custom logging
"""
import enum
import logging
import os
import uuid
from logging.config import fileConfig

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import anyio

from app.middleware.formatter import RequestFormatter
from app.utils.log_util import pretty_print_for_dev, pretty_print_json
from config import constants as const


# Creating enumerations using class
class Mode(enum.Enum):
    """
    Mode selection class
    """

    DEV = "dev"
    FULL = "full"
    PROD = "prod"


LOGDIR = const.LOGS_DIR
if not os.path.exists(LOGDIR):
    os.makedirs(LOGDIR, exist_ok=True)

fileConfig(
    os.path.join(const.PROJECT_ROOT_DIR, const.CONFIG_DIR, const.LOGGING_CONF),
    disable_existing_loggers=False,
)

log = logging.getLogger(const.LOGGING_CONF)


def logger() -> logging.Logger:
    """
    log function to return log instance
    """
    return log


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Logger middleware for FastAPI applications.
    Logs request details, exceptions, and handles mode-specific logging.
    """

    def __init__(self, app: FastAPI, mode: Mode):
        """
        Initialize the Logger with mode-specific settings.
        Args:
            app : FastAPI app.
            mode: Mode (dev, prod, or full)
        """
        super().__init__(app)
        self.mode = mode
        self.min_log_level = self.get_min_log_level()
        formatter = RequestFormatter(const.LOG_FORMAT)

        # Apply formatter to all log handlers
        for handler in log.handlers:
            handler.setFormatter(formatter)

        logger().setLevel(self.min_log_level)
        log.info("Logger initialized in %s mode.", self.mode.value)

    async def dispatch(self, request: Request, call_next):
        """
        Middleware to handle requests and log exceptions.
        """
        request_id = str(uuid.uuid4())
        structlog.threadlocal.clear_threadlocal()
        structlog.threadlocal.bind_threadlocal(
            url=str(request.url),
            method=request.method,
            request_id=request_id,
        )

        try:
            # Log request information
            log.info(
                "Processing request %s %s with ID %s",
                request.method,
                request.url,
                request_id,
                extra={"request": request},
            )

            # Call the next middleware or route handler
            response = await call_next(request)
            response.headers["request_id"] = request_id

            # Log the response status
            log.info(
                "Request %s processed successfully with status code %s",
                request_id,
                response.status_code,
                extra={"request": request},
            )
            return response

        except anyio.EndOfStream:
            # Handle end of stream errors specifically
            log.warning("End of stream reached for request %s.", request_id)
            raise

        except anyio.WouldBlock as exc:
            # Handle would-block errors (e.g., blocking IO issues)
            log.warning("Request %s blocked: %s", request_id, exc)
            raise

        except Exception as exc:
            # Log any unexpected errors and re-raise the exception
            log.error(
                "Error processing request %s: %s",
                request_id,
                exc,
                exc_info=True,
                extra={"request": request},
            )
            # Check if this is an ExceptionGroup, which might be from a TaskGroup
            if type(exc).__name__ == "ExceptionGroup":
                # Extract the first exception from the group for a cleaner error message
                if exc.__cause__ is not None:
                    raise exc.__cause__ from None
                if hasattr(exc, "exceptions") and len(exc.exceptions) > 0:
                    raise exc.exceptions[0] from None
            raise exc

    def get_print_fn(self):
        """
        Return the print function based on the current mode.
        In DEV and FULL mode, pretty print for developers.
        In PROD mode, log in JSON format.
        """
        if self.mode == Mode.DEV:
            return pretty_print_for_dev
        if self.mode == Mode.FULL:
            return pretty_print_json
        return pretty_print_for_dev

    def get_min_log_level(self) -> int:
        """
        Return the minimum log level based on the mode.
        DEV mode: DEBUG level logging.
        PROD mode: INFO level logging.
        FULL mode: INFO level logging.
        """
        if self.mode == Mode.DEV:
            return logging.DEBUG
        if self.mode == Mode.PROD:
            return logging.INFO
        return logging.INFO
