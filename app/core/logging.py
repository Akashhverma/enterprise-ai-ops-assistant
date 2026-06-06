from __future__ import annotations

import logging

from .config import get_settings


def configure_api_logging() -> logging.Logger:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("enterprise_ai_ops.api")

