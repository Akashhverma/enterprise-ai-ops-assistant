from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_api_logging


logger = configure_api_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "api_start app=%s version=%s environment=%s",
        settings.app_name,
        settings.version,
        settings.environment,
    )
    yield
    logger.info("api_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "FastAPI backend for the Enterprise AI Operations Assistant. "
            "It exposes LangGraph-powered query/chat APIs plus ticket and log search endpoints."
        ),
        lifespan=lifespan,
        contact={"name": "AI Operations Platform"},
        openapi_tags=[
            {"name": "system", "description": "Service health and metadata."},
            {"name": "assistant", "description": "LangGraph-powered assistant APIs."},
            {"name": "data", "description": "Enterprise ticket and deployment-log access."},
        ],
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()

