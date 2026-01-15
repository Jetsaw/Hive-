from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.core.config import settings
from app.memory.db import init_db
from app.agents import IngestionAgent, Trace

from app.api.health import router as health_router
from app.api.chat import router as chat_router
import app.api.chat as chat_module


def create_app() -> FastAPI:
    setup_logging()
    init_db()

    app = FastAPI(title="HIVE Backend", version="1.0")

    # When running behind nginx (localhost:8080), frontend calls /api/* (same origin).
    # But we still allow origin for direct testing if needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Build/load preloaded global KB index
    ingestion = IngestionAgent()
    trace = Trace()
    index, metas = ingestion.build_or_load(trace)
    chat_module.GLOBAL_INDEX = index
    chat_module.GLOBAL_METAS = metas

    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app


app = create_app()
