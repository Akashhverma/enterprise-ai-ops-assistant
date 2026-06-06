from __future__ import annotations

import logging

from .config import get_log_level


def configure_logging(logger_name: str) -> logging.Logger:
    logging.basicConfig(
        level=get_log_level(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger(logger_name)

