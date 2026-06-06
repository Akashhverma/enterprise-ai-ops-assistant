from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FrontendSettings:
    api_base_url: str
    request_timeout_seconds: float


def get_frontend_settings() -> FrontendSettings:
    return FrontendSettings(
        api_base_url=os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        request_timeout_seconds=float(os.getenv("STREAMLIT_REQUEST_TIMEOUT_SECONDS", "45")),
    )

