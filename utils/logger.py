
import logging
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import LOG_FILE


class JSONFormatter(logging.Formatter):
    """Format logs as structured JSON."""

    def format(self, record):

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "system"),
            "module": record.name,
        }

        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger():
    """Configure application logging."""

    logger = logging.getLogger("DigiPlus")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    Path(LOG_FILE).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    file_handler.setFormatter(JSONFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def new_request_id():
    """Generate a unique request ID."""

    return str(uuid.uuid4())


def log_event(message, level="INFO", request_id="system"):
    """Write a structured application event."""

    extra = {"request_id": request_id}

    if level == "ERROR":
        logger.error(message, extra=extra)

    elif level == "WARNING":
        logger.warning(message, extra=extra)

    else:
        logger.info(message, extra=extra)
